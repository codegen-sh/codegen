from __future__ import annotations

import os
from collections import Counter, defaultdict
from contextlib import contextmanager
from enum import IntEnum, auto, unique
from functools import lru_cache
from os import PathLike
from pathlib import Path
from typing import TYPE_CHECKING, Any

from rustworkx import PyDiGraph, WeightedEdgeList

from codegen.configs.models.codebase import CodebaseConfig, PinkMode
from codegen.configs.models.secrets import SecretsConfig
from codegen.sdk.codebase.config import ProjectConfig, SessionOptions
from codegen.sdk.codebase.config_parser import ConfigParser, get_config_parser_for_language
from codegen.sdk.codebase.diff_lite import ChangeType, DiffLite
from codegen.sdk.codebase.flagging.flags import Flags
from codegen.sdk.codebase.io.file_io import FileIO
from codegen.sdk.codebase.progress.stub_progress import StubProgress
from codegen.sdk.codebase.transaction_manager import TransactionManager
from codegen.sdk.codebase.validation import get_edges, post_reset_validation
from codegen.sdk.core.autocommit import AutoCommit, commiter
from codegen.sdk.core.directory import Directory
from codegen.sdk.core.external.dependency_manager import DependencyManager, get_dependency_manager
from codegen.sdk.core.external.language_engine import LanguageEngine, get_language_engine
from codegen.sdk.enums import Edge, EdgeType, NodeType
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.extensions.utils import uncache_all
from codegen.sdk.typescript.external.ts_declassify.ts_declassify import TSDeclassify
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.exceptions.control_flow import StopCodemodException
from codegen.shared.logging.get_logger import get_logger
from codegen.shared.performance.stopwatch_utils import stopwatch, stopwatch_with_sentry

if TYPE_CHECKING:
    from collections.abc import Generator, Mapping, Sequence

    from codeowners import CodeOwners as CodeOwnersParser
    from git import Commit as GitCommit

    from codegen.git.repo_operator.repo_operator import RepoOperator
    from codegen.sdk.codebase.io.io import IO
    from codegen.sdk.codebase.node_classes.node_classes import NodeClasses
    from codegen.sdk.codebase.progress.progress import Progress
    from codegen.sdk.core.dataclasses.usage import Usage
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.external_module import ExternalModule
    from codegen.sdk.core.file import File, SourceFile
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.parser import Parser

logger = get_logger(__name__)


# src/vs/platform/contextview/browser/contextMenuService.ts is ignored as there is a parsing error with tree-sitter
GLOBAL_FILE_IGNORE_LIST = [
    ".git/*",
    "*/.git/*",
    "node_modules/*",
    "*/node_modules/*",
    ".yarn/releases/*",
    ".*/tests/static/chunk-.*.js",
    ".*/ace/.*.js",
    "src/vs/platform/contextview/browser/contextMenuService.ts",
    "*/semver.js",
    "*/compiled/*",
    "*.min.js",
    "*@*.js",
]


@unique
class SyncType(IntEnum):
    DELETE = auto()
    REPARSE = auto()
    ADD = auto()


def get_node_classes(programming_language: ProgrammingLanguage) -> NodeClasses:
    if programming_language == ProgrammingLanguage.PYTHON:
        from codegen.sdk.codebase.node_classes.py_node_classes import PyNodeClasses

        return PyNodeClasses
    elif programming_language == ProgrammingLanguage.TYPESCRIPT:
        from codegen.sdk.codebase.node_classes.ts_node_classes import TSNodeClasses

        return TSNodeClasses
    else:
        from codegen.sdk.codebase.node_classes.generic_node_classes import GenericNodeClasses

        return GenericNodeClasses


class CodebaseContext:
    """MultiDiGraph Wrapper with TransactionManager"""

    # =====[ __init__ attributes ]=====
    node_classes: NodeClasses
    programming_language: ProgrammingLanguage
    repo_path: str
    repo_name: str
    codeowners_parser: CodeOwnersParser | None
    config: CodebaseConfig
    secrets: SecretsConfig

    # =====[ computed attributes ]=====
    transaction_manager: TransactionManager
    pending_syncs: list[DiffLite]  # Diffs that have been applied to disk, but not the graph (to be used for sync graph)
    all_syncs: list[DiffLite]  # All diffs that have been applied to the graph (to be used for graph reset)
    _autocommit: AutoCommit
    generation: int
    parser: Parser[Expression]
    synced_commit: GitCommit | None
    directories: dict[Path, Directory]
    base_url: str | None
    extensions: list[str]
    config_parser: ConfigParser | None
    dependency_manager: DependencyManager | None
    language_engine: LanguageEngine | None
    _computing = False
    _graph: PyDiGraph[Importable, Edge]
    filepath_idx: dict[str, NodeId]
    _ext_module_idx: dict[str, NodeId]
    flags: Flags
    session_options: SessionOptions = SessionOptions()
    projects: list[ProjectConfig]
    unapplied_diffs: list[DiffLite]
    io: IO
    progress: Progress

    def __init__(
        self,
        projects: list[ProjectConfig],
        config: CodebaseConfig | None = None,
        secrets: SecretsConfig | None = None,
        io: IO | None = None,
        progress: Progress | None = None,
    ) -> None:
        """Initializes codebase graph and TransactionManager"""
        from codegen.sdk.core.parser import Parser

        self.progress = progress or StubProgress()
        self.__graph = PyDiGraph()
        self.__graph_ready = False
        self.filepath_idx = {}
        self._ext_module_idx = {}
        self.generation = 0

        # NOTE: The differences between base_path, repo_name, and repo_path
        # /home/codegen/projects/my-project/src
        #                                   ^^^  <-  Base Path (Optional)
        #                        ^^^^^^^^^^  <-----  Repo Name
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  <-----  Repo Path
        # ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  <-  Full Path
        # (full_path is unused for CGB, but is used elsewhere.)

        # =====[ __init__ attributes ]=====
        self.projects = projects
        context = projects[0]
        self.node_classes = get_node_classes(context.programming_language)
        self.config = config or CodebaseConfig()
        self.secrets = secrets or SecretsConfig()
        self.repo_name = context.repo_operator.repo_name
        self.repo_path = str(Path(context.repo_operator.repo_path).resolve())
        self.full_path = os.path.join(self.repo_path, context.base_path) if context.base_path else self.repo_path
        self.codeowners_parser = context.repo_operator.codeowners_parser
        self.base_url = context.repo_operator.base_url
        if not self.config.allow_external:
            # TODO: Fix this to be more robust with multiple projects
            self.io = io or FileIO(allowed_paths=[Path(self.repo_path).resolve()])
        else:
            self.io = io or FileIO()
        # =====[ computed attributes ]=====
        self.transaction_manager = TransactionManager()
        self._autocommit = AutoCommit(self)
        self.init_nodes = None
        self.init_edges = None
        self.directories = dict()
        self.parser = Parser.from_node_classes(self.node_classes, log_parse_warnings=self.config.debug)
        self.extensions = self.node_classes.file_cls.get_extensions()
        # ORDER IS IMPORTANT HERE!
        self.config_parser = get_config_parser_for_language(context.programming_language, self)
        self.dependency_manager = get_dependency_manager(context.programming_language, self)
        self.language_engine = get_language_engine(context.programming_language, self)
        self.programming_language = context.programming_language

        # Raise warning if language is not supported
        if self.programming_language is ProgrammingLanguage.UNSUPPORTED or self.programming_language is ProgrammingLanguage.OTHER:
            logger.warning("WARNING: The codebase is using an unsupported language!")
            logger.warning("Some features may not work as expected. Advanced static analysis will be disabled but simple file IO will still work.")

        # Assert config assertions
        # External import resolution must be enabled if syspath is enabled
        if self.config.py_resolve_syspath:
            if not self.config.allow_external:
                msg = "allow_external must be set to True when py_resolve_syspath is enabled"
                raise ValueError(msg)

        # Build the graph
        if not self.config.exp_lazy_graph and self.config.use_pink != PinkMode.ALL_FILES:
            self.build_graph(context.repo_operator)
        try:
            self.synced_commit = context.repo_operator.head_commit
        except ValueError as e:
            logger.exception("Error getting commit head %s", e)
            self.synced_commit = None
        self.pending_syncs = []
        self.all_syncs = []
        self.unapplied_diffs = []
        self.flags = Flags()

    def __repr__(self):
        return self.__class__.__name__

    @property
    def _graph(self) -> PyDiGraph[Importable, Edge]:
        if not self.__graph_ready:
            logger.info("Lazily Computing Graph")
            self.build_graph(self.projects[0].repo_operator)
        return self.__graph

    @_graph.setter
    def _graph(self, value: PyDiGraph[Importable, Edge]) -> None:
        self.__graph = value

    @stopwatch_with_sentry(name="build_graph")
    @commiter
    def build_graph(self, repo_operator: RepoOperator) -> None:
        """Builds a codebase graph based on the current file state of the given repo operator"""
        self.__graph_ready = True
        self._graph.clear()

        # =====[ Add all files to the graph in parallel ]=====
        syncs = defaultdict(lambda: [])
        if self.config.disable_file_parse:
            logger.warning("WARNING: File parsing is disabled!")
        else:
            for filepath, _ in repo_operator.iter_files(subdirs=self.projects[0].subdirectories, extensions=self.extensions, ignore_list=GLOBAL_FILE_IGNORE_LIST):
                syncs[SyncType.ADD].append(self.to_absolute(filepath))
        logger.info(f"> Parsing {len(syncs[SyncType.ADD])} files in {self.projects[0].subdirectories or 'ALL'} subdirectories with {self.extensions} extensions")
        self._process_diff_files(syncs, incremental=False)
        files: list[SourceFile] = self.get_nodes(NodeType.FILE)
        logger.info(f"> Found {len(files)} files")
        logger.info(f"> Found {len(self.nodes)} nodes and {len(self.edges)} edges")
        if self.config.track_graph:
            self.old_graph = self._graph.copy()

    @stopwatch
    @commiter
    def apply_diffs(self, diff_list: list[DiffLite]) -> None:
        """Applies the given set of diffs to the graph in order to match the current file system content"""
        if self.session_options:
            self.session_options = self.session_options.model_copy(update={"max_seconds": None})
        logger.info(f"Applying {len(diff_list)} diffs to graph")
        files_to_sync: dict[Path, SyncType] = {}
        # Gather list of deleted files, new files to add, and modified files to reparse
        file_cls = self.node_classes.file_cls
        extensions = file_cls.get_extensions()
        for diff in diff_list:
            filepath = Path(diff.path)
            if extensions is not None and filepath.suffix not in extensions:
                continue
            if self.projects[0].subdirectories is not None and not any(filepath.relative_to(subdir) for subdir in self.projects[0].subdirectories):
                continue

            if diff.change_type == ChangeType.Added:
                # Sync by adding the added file to the graph
                files_to_sync[filepath] = SyncType.ADD
            elif diff.change_type == ChangeType.Modified:
                files_to_sync[filepath] = SyncType.REPARSE
            elif diff.change_type == ChangeType.Renamed:
                files_to_sync[diff.rename_from] = SyncType.DELETE
                files_to_sync[diff.rename_to] = SyncType.ADD
            elif diff.change_type == ChangeType.Removed:
                files_to_sync[filepath] = SyncType.DELETE
            else:
                logger.warning(f"Unhandled diff change type: {diff.change_type}")
        by_sync_type = defaultdict(lambda: [])
        if self.config.disable_file_parse:
            logger.warning("WARNING: File parsing is disabled!")
        else:
            for filepath, sync_type in files_to_sync.items():
                if self.get_file(filepath) is None:
                    if sync_type is SyncType.DELETE:
                        # SourceFile is already deleted, nothing to do here
                        continue
                    elif sync_type is SyncType.REPARSE:
                        # SourceFile needs to be parsed for the first time
                        sync_type = SyncType.ADD
                elif sync_type is SyncType.ADD:
                    # If the file was deleted earlier, we need to reparse so we can remove old edges
                    sync_type = SyncType.REPARSE

                by_sync_type[sync_type].append(filepath)
        self.generation += 1
        self._process_diff_files(by_sync_type)

    def _reset_files(self, syncs: list[DiffLite]) -> None:
        files_to_write = []
        files_to_remove = []
        modified_files = set()
        for sync in syncs:
            if sync.path in modified_files:
                continue
            if sync.change_type == ChangeType.Removed:
                files_to_write.append((sync.path, sync.old_content))
                modified_files.add(sync.path)
                logger.info(f"Removing {sync.path} from disk")
            elif sync.change_type == ChangeType.Modified:
                files_to_write.append((sync.path, sync.old_content))
                modified_files.add(sync.path)
            elif sync.change_type == ChangeType.Renamed:
                files_to_write.append((sync.rename_from, sync.old_content))
                files_to_remove.append(sync.rename_to)
                modified_files.add(sync.rename_from)
                modified_files.add(sync.rename_to)
            elif sync.change_type == ChangeType.Added:
                files_to_remove.append(sync.path)
                modified_files.add(sync.path)
        logger.info(f"Writing {len(files_to_write)} files to disk and removing {len(files_to_remove)} files")
        for file in files_to_remove:
            self.io.delete_file(file)
        to_save = set()
        for file, content in files_to_write:
            self.io.write_file(file, content)
            to_save.add(file)
        self.io.save_files(to_save)

    @stopwatch
    def reset_codebase(self) -> None:
        self._reset_files(self.all_syncs + self.pending_syncs + self.unapplied_diffs)
        self.unapplied_diffs.clear()

    @stopwatch
    def undo_applied_diffs(self) -> None:
        self.transaction_manager.clear_transactions()
        self.reset_codebase()
        self.io.check_changes()
        self.pending_syncs.clear()  # Discard pending changes
        if len(self.all_syncs) > 0:
            logger.info(f"Unapplying {len(self.all_syncs)} diffs to graph. Current graph commit: {self.synced_commit}")
            self._revert_diffs(list(reversed(self.all_syncs)))
        self.all_syncs.clear()

    @stopwatch
    @commiter(reset=True)
    def _revert_diffs(self, diff_list: list[DiffLite]) -> None:
        """Resets the graph to its initial solve branch file state"""
        reversed_diff_list = list(DiffLite.from_reverse_diff(diff) for diff in diff_list)
        self._autocommit.reset()
        self.apply_diffs(reversed_diff_list)
        # ====== [ Re-resolve lost edges from previous syncs ] ======
        self.prune_graph()
        if self.config.verify_graph:
            post_reset_validation(self.old_graph.nodes(), self._graph.nodes(), get_edges(self.old_graph), get_edges(self._graph), self.repo_name, self.projects[0].subdirectories)

    def save_commit(self, commit: GitCommit) -> None:
        if commit is not None:
            logger.info(f"Saving commit {commit.hexsha} to graph")
            self.all_syncs.clear()
            self.unapplied_diffs.clear()
            self.synced_commit = commit
            if self.config.verify_graph:
                self.old_graph = self._graph.copy()

    @stopwatch
    def prune_graph(self) -> None:
        # ====== [ Remove orphaned external modules ] ======
        external_modules = self.get_nodes(NodeType.EXTERNAL)
        for module in external_modules:
            if not any(self.predecessors(module.node_id)):
                self.remove_node(module.node_id)
                self._ext_module_idx.pop(module._idx_key, None)

    def build_directory_tree(self) -> None:
        """Builds the directory tree for the codebase"""
        # Reset and rebuild the directory tree
        self.directories = dict()

        for file_path, _ in self.projects[0].repo_operator.iter_files(
            subdirs=self.projects[0].subdirectories,
            ignore_list=GLOBAL_FILE_IGNORE_LIST,
            skip_content=True,
        ):
            file_path = Path(file_path)
            directory = self.get_directory(file_path.parent, create_on_missing=True)
            directory._add_file(file_path.name)

    def get_directory(self, directory_path: PathLike, create_on_missing: bool = False, ignore_case: bool = False) -> Directory | None:
        """Returns the directory object for the given path, or None if the directory does not exist.

        If create_on_missing is set, use a recursive strategy to create the directory object and all subdirectories.
        """
        # If not part of repo path, return None
        absolute_path = self.to_absolute(directory_path)
        if not self.is_subdir(absolute_path) and not self.config.allow_external:
            assert False, f"Directory {absolute_path} is not part of repo path {self.repo_path}"
            return None

        # Get the directory
        if dir := self.directories.get(absolute_path, None):
            return dir
        if ignore_case:
            for path, directory in self.directories.items():
                if str(absolute_path).lower() == str(path).lower():
                    return directory

        # If the directory does not exist, create it
        if create_on_missing:
            # Get the parent directory and create it if it does not exist
            parent_path = absolute_path.parent

            # Base Case
            if str(absolute_path) == str(self.repo_path) or str(absolute_path) == str(parent_path):
                root_directory = Directory(ctx=self, path=absolute_path, dirpath="")
                self.directories[absolute_path] = root_directory
                return root_directory

            # Recursively create the parent directory
            parent = self.get_directory(parent_path, create_on_missing=True)
            # Create the directory
            directory = Directory(ctx=self, path=absolute_path, dirpath=str(self.to_relative(absolute_path)))
            # Add the directory to the parent
            parent._add_subdirectory(directory.name)
            # Add the directory to the tree
            self.directories[absolute_path] = directory
            return directory
        return None

    def _process_diff_files(self, files_to_sync: Mapping[SyncType, list[Path]], incremental: bool = True) -> None:
        # If all the files are empty, don't uncache
        assert self._computing is False
        skip_uncache = incremental and ((len(files_to_sync[SyncType.DELETE]) + len(files_to_sync[SyncType.REPARSE])) == 0)
        if not skip_uncache:
            uncache_all()
        # Step 0: Start the dependency manager and language engine if they exist
        # Start the dependency manager. This may or may not run asynchronously, depending on the implementation
        if self.dependency_manager is not None:
            # Check if its inital start or a reparse
            if not self.dependency_manager.ready() and not self.dependency_manager.error():
                # TODO: We do not reparse dependencies during syncs as it is expensive. We should probably add a flag for this
                logger.info("> Starting dependency manager")
                self.dependency_manager.start(async_start=False)

        # Start the language engine. This may or may not run asynchronously, depending on the implementation
        if self.language_engine is not None:
            # Check if its inital start or a reparse
            if not self.language_engine.ready() and not self.language_engine.error():
                logger.info("> Starting language engine")
                self.language_engine.start(async_start=False)
            else:
                logger.info("> Reparsing language engine")
                self.language_engine.reparse(async_start=False)

        # Step 1: Wait for dependency manager and language engines to finish before graph construction
        if self.dependency_manager is not None:
            self.dependency_manager.wait_until_ready(ignore_error=self.config.ignore_process_errors)
        if self.language_engine is not None:
            self.language_engine.wait_until_ready(ignore_error=self.config.ignore_process_errors)

        # ====== [ Refresh the graph] ========
        # Step 2: For any files that no longer exist, remove them during the sync
        add_to_remove = []
        if incremental:
            for file_path in files_to_sync[SyncType.ADD]:
                if not self.io.file_exists(self.to_absolute(file_path)):
                    add_to_remove.append(file_path)
                    logger.warning(f"SYNC: SourceFile {file_path} no longer exists! Removing from graph")
            reparse_to_remove = []
            for file_path in files_to_sync[SyncType.REPARSE]:
                if not self.io.file_exists(self.to_absolute(file_path)):
                    reparse_to_remove.append(file_path)
                    logger.warning(f"SYNC: SourceFile {file_path} no longer exists! Removing from graph")
            files_to_sync[SyncType.ADD] = [f for f in files_to_sync[SyncType.ADD] if f not in add_to_remove]
            files_to_sync[SyncType.REPARSE] = [f for f in files_to_sync[SyncType.REPARSE] if f not in reparse_to_remove]
            for file_path in add_to_remove + reparse_to_remove:
                if self.get_file(file_path) is not None:
                    files_to_sync[SyncType.DELETE].append(file_path)
                else:
                    logger.warning(f"SYNC: SourceFile {file_path} does not exist and also not found on graph!")

        # Step 3: Remove files to delete from graph
        to_resolve = []
        for file_path in files_to_sync[SyncType.DELETE]:
            file = self.get_file(file_path)
            file.remove_internal_edges()
            to_resolve.extend(file.unparse())
        to_resolve = list(filter(lambda node: self.has_node(node.node_id) and node is not None, to_resolve))
        for file_path in files_to_sync[SyncType.REPARSE]:
            file = self.get_file(file_path)
            file.remove_internal_edges()

        task = self.progress.begin("Reparsing updated files", count=len(files_to_sync[SyncType.REPARSE]))
        files_to_resolve = []
        # Step 4: Reparse updated files
        for idx, file_path in enumerate(files_to_sync[SyncType.REPARSE]):
            task.update(f"Reparsing {self.to_relative(file_path)}", count=idx)
            file = self.get_file(file_path)
            to_resolve.extend(file.unparse(reparse=True))
            to_resolve = list(filter(lambda node: self.has_node(node.node_id) and node is not None, to_resolve))
            file.sync_with_file_content()
            files_to_resolve.append(file)
        task.end()
        # Step 5: Add new files as nodes to graph (does not yet add edges)
        task = self.progress.begin("Adding new files", count=len(files_to_sync[SyncType.ADD]))
        for idx, filepath in enumerate(files_to_sync[SyncType.ADD]):
            task.update(f"Adding {self.to_relative(filepath)}", count=idx)
            try:
                content = self.io.read_text(filepath)
            except UnicodeDecodeError as e:
                logger.warning(f"Can't read file at:{filepath} since it contains non-unicode characters. File will be ignored!")
                continue
            # TODO: this is wrong with context changes
            if filepath.suffix in self.extensions:
                file_cls = self.node_classes.file_cls
                new_file = file_cls.from_content(filepath, content, self, sync=False, verify_syntax=False)
                if new_file is not None:
                    files_to_resolve.append(new_file)
        task.end()
        for file in files_to_resolve:
            to_resolve.append(file)
            to_resolve.extend(file.get_nodes())

        to_resolve = list(filter(lambda node: self.has_node(node.node_id) and node is not None, to_resolve))
        counter = Counter(node.node_type for node in to_resolve)

        # Step 6: Build directory tree
        logger.info("> Building directory tree")
        self.build_directory_tree()

        # Step 7: Build configs
        if self.config_parser is not None:
            self.config_parser.parse_configs()

        # Step 8: Add internal import resolution edges for new and updated files
        if not skip_uncache:
            uncache_all()

        if self.config.disable_graph:
            logger.warning("Graph generation is disabled. Skipping import and symbol resolution")
            self._computing = False
        else:
            self._computing = True
            try:
                logger.info(f"> Computing import resolution edges for {counter[NodeType.IMPORT]} imports")
                task = self.progress.begin("Resolving imports", count=counter[NodeType.IMPORT])
                for node in to_resolve:
                    if node.node_type == NodeType.IMPORT:
                        task.update(f"Resolving imports in {node.filepath}", count=idx)
                        node._remove_internal_edges(EdgeType.IMPORT_SYMBOL_RESOLUTION)
                        node.add_symbol_resolution_edge()
                        to_resolve.extend(node.symbol_usages)
                task.end()
                if counter[NodeType.EXPORT] > 0:
                    logger.info(f"> Computing export dependencies for {counter[NodeType.EXPORT]} exports")
                    task = self.progress.begin("Computing export dependencies", count=counter[NodeType.EXPORT])
                    for node in to_resolve:
                        if node.node_type == NodeType.EXPORT:
                            task.update(f"Computing export dependencies for {node.filepath}", count=idx)
                            node._remove_internal_edges(EdgeType.EXPORT)
                            node.compute_export_dependencies()
                            to_resolve.extend(node.symbol_usages)
                    task.end()
                if counter[NodeType.SYMBOL] > 0:
                    from codegen.sdk.core.interfaces.inherits import Inherits

                    logger.info("> Computing superclass dependencies")
                    task = self.progress.begin("Computing superclass dependencies", count=counter[NodeType.SYMBOL])
                    for symbol in to_resolve:
                        if isinstance(symbol, Inherits):
                            task.update(f"Computing superclass dependencies for {symbol.filepath}", count=idx)
                            symbol._remove_internal_edges(EdgeType.SUBCLASS)
                            symbol.compute_superclass_dependencies()
                    task.end()
                if not skip_uncache:
                    uncache_all()
                self._compute_dependencies(to_resolve, incremental)
            finally:
                self._computing = False

    def _compute_dependencies(self, to_update: list[Importable], incremental: bool):
        seen = set()
        while to_update:
            task = self.progress.begin("Computing dependencies", count=len(to_update))
            step = to_update.copy()
            to_update.clear()
            logger.info(f"> Incrementally computing dependencies for {len(step)} nodes")
            for idx, current in enumerate(step):
                task.update(f"Computing dependencies for {current.filepath}", count=idx)
                if current not in seen:
                    seen.add(current)
                    to_update.extend(current.recompute(incremental))
            if not incremental:
                for node in self._graph.nodes():
                    if node not in seen:
                        to_update.append(node)
            task.end()
        seen.clear()

    def build_subgraph(self, nodes: list[NodeId]) -> PyDiGraph[Importable, Edge]:
        """Builds a subgraph from the given set of nodes"""
        subgraph = PyDiGraph()
        subgraph.add_nodes_from(self._graph.nodes())
        subgraph.add_edges_from(self._graph.weighted_edge_list())
        return subgraph.subgraph(nodes)

    def get_node(self, node_id: int) -> Any:
        return self._graph.get_node_data(node_id)

    def get_nodes(self, node_type: NodeType | None = None, exclude_type: NodeType | None = None) -> list[Importable]:
        if node_type is not None and exclude_type is not None:
            msg = "node_type and exclude_type cannot both be specified"
            raise ValueError(msg)
        if node_type is not None:
            return [self.get_node(node_id) for node_id in self._graph.filter_nodes(lambda node: node.node_type == node_type)]
        if exclude_type is not None:
            return [self.get_node(node_id) for node_id in self._graph.filter_nodes(lambda node: node.node_type != node_type)]
        return self._graph.nodes()

    def get_edges(self) -> list[tuple[NodeId, NodeId, EdgeType, Usage | None]]:
        return [(x[0], x[1], x[2].type, x[2].usage) for x in self._graph.weighted_edge_list()]

    def get_file(self, file_path: os.PathLike, ignore_case: bool = False) -> SourceFile | None:
        # If not part of repo path, return None
        absolute_path = self.to_absolute(file_path)
        if not self.is_subdir(absolute_path) and not self.config.allow_external:
            assert False, f"File {file_path} is not part of the repository path"

        # Check if file exists in graph
        node_id = self.filepath_idx.get(str(self.to_relative(file_path)), None)
        if node_id is not None:
            return self.get_node(node_id)
        if ignore_case:
            # Using `get_directory` so that the case insensitive lookup works
            parent = self.get_directory(self.to_absolute(file_path).parent, ignore_case=ignore_case).path
            for file in parent.iterdir():
                if str(file_path).lower() == str(self.to_relative(file)).lower():
                    return self.get_file(file, ignore_case=False)

    def _get_raw_file_from_path(self, path: Path) -> File | None:
        from codegen.sdk.core.file import File

        try:
            return File.from_content(path, self.io.read_text(path), self, sync=False)
        except UnicodeDecodeError:
            # Handle when file is a binary file
            return File.from_content(path, self.io.read_bytes(path), self, sync=False, binary=True)

    def get_external_module(self, module: str, import_name: str) -> ExternalModule | None:
        node_id = self._ext_module_idx.get(module + "::" + import_name, None)
        if node_id is not None:
            return self.get_node(node_id)

    def add_node(self, node: Importable) -> int:
        if self.config.debug:
            if self._graph.find_node_by_weight(node.__eq__):
                msg = "Node already exists"
                raise Exception(msg)
        if self.config.debug and self._computing and node.node_type != NodeType.EXTERNAL:
            assert False, f"Adding node during compute dependencies: {node!r}"
        return self._graph.add_node(node)

    def add_child(self, parent: NodeId, node: Importable, type: EdgeType, usage: Usage | None = None) -> int:
        if self.config.debug:
            if self._graph.find_node_by_weight(node.__eq__):
                msg = "Node already exists"
                raise Exception(msg)
        if self.config.debug and self._computing and node.node_type != NodeType.EXTERNAL:
            assert False, f"Adding node during compute dependencies: {node!r}"
        return self._graph.add_child(parent, node, Edge(type, usage))

    def has_node(self, node_id: NodeId):
        return isinstance(node_id, int) and self._graph.has_node(node_id)

    def has_edge(self, u: NodeId, v: NodeId, edge: Edge):
        return self._graph.has_edge(u, v) and edge in self._graph.get_all_edge_data(u, v)

    def add_edge(self, u: NodeId, v: NodeId, type: EdgeType, usage: Usage | None = None) -> None:
        edge = Edge(type, usage)
        if self.config.debug:
            assert self._graph.has_node(u)
            assert self._graph.has_node(v), v
            assert not self.has_edge(u, v, edge), (u, v, edge)
        self._graph.add_edge(u, v, edge)

    def add_edges(self, edges: list[tuple[NodeId, NodeId, Edge]]) -> None:
        if self.config.debug:
            for u, v, edge in edges:
                assert self._graph.has_node(u)
                assert self._graph.has_node(v), v
                assert not self.has_edge(u, v, edge), (self.get_node(u), self.get_node(v), edge)
        self._graph.add_edges_from(edges)

    @property
    def nodes(self):
        return self._graph.nodes()

    @property
    def edges(self) -> WeightedEdgeList[Edge]:
        return self._graph.weighted_edge_list()

    def predecessor(self, n: NodeId, *, edge_type: EdgeType | None) -> Importable:
        return self._graph.find_predecessor_node_by_edge(n, lambda edge: edge.type == edge_type)

    def predecessors(self, n: NodeId, edge_type: EdgeType | None = None) -> Sequence[Importable]:
        if edge_type is not None:
            return sort_editables(self._graph.find_predecessors_by_edge(n, lambda edge: edge.type == edge_type), by_id=True)
        return self._graph.predecessors(n)

    def successors(self, n: NodeId, *, edge_type: EdgeType | None = None, sort: bool = True) -> Sequence[Importable]:
        if edge_type is not None:
            res = self._graph.find_successors_by_edge(n, lambda edge: edge.type == edge_type)
        else:
            res = self._graph.successors(n)
        if sort:
            return sort_editables(res, by_id=True, dedupe=False)
        return res

    def get_edge_data(self, *args, **kwargs) -> set[Edge]:
        return set(self._graph.get_all_edge_data(*args, **kwargs))

    def in_edges(self, n: NodeId) -> WeightedEdgeList[Edge]:
        return self._graph.in_edges(n)

    def out_edges(self, n: NodeId) -> WeightedEdgeList[Edge]:
        return self._graph.out_edges(n)

    def remove_node(self, n: NodeId):
        return self._graph.remove_node(n)

    def remove_edge(self, u: NodeId, v: NodeId, *, edge_type: EdgeType | None = None):
        for edge in self._graph.edge_indices_from_endpoints(u, v):
            if edge_type is not None:
                if self._graph.get_edge_data_by_index(edge).type != edge_type:
                    continue
            self._graph.remove_edge_from_index(edge)

    @lru_cache(maxsize=10000)
    def to_absolute(self, filepath: PathLike | str) -> Path:
        path = Path(filepath)
        if not path.is_absolute():
            path = Path(self.repo_path) / path
        return path.resolve()

    @lru_cache(maxsize=10000)
    def to_relative(self, filepath: PathLike | str) -> Path:
        path = self.to_absolute(filepath)
        if path == Path(self.repo_path) or Path(self.repo_path) in path.parents:
            return path.relative_to(self.repo_path)
        return path

    def is_subdir(self, path: PathLike | str) -> bool:
        path = self.to_absolute(path)
        return path == Path(self.repo_path) or path.is_relative_to(self.repo_path) or Path(self.repo_path) in path.parents

    @commiter
    def commit_transactions(self, sync_graph: bool = True, sync_file: bool = True, files: set[Path] | None = None) -> None:
        """Commits all transactions to the codebase, and syncs the graph to match the latest file changes.
        Should be called at the end of `execute` for every codemod group run.

        Arguments:
            sync_graph (bool): If True, syncs the graph with the latest set of file changes
            sync_file (bool): If True, writes any pending file edits to the file system
            files (set[str] | None): If provided, only commits transactions for the given set of files
        """
        # Commit transactions for all contexts
        files_to_lock = self.transaction_manager.to_commit(files)
        diffs = self.transaction_manager.commit(files_to_lock)
        for diff in diffs:
            if self.get_file(diff.path) is None:
                self.unapplied_diffs.append(diff)
            else:
                self.pending_syncs.append(diff)

        # Write files if requested
        if sync_file:
            self.io.save_files(files)

        # Sync the graph if requested
        if sync_graph and len(self.pending_syncs) > 0:
            self.apply_diffs(self.pending_syncs)
            self.all_syncs.extend(self.pending_syncs)
            self.pending_syncs.clear()

    @commiter
    def add_single_file(self, filepath: PathLike) -> None:
        """Adds a file to the graph and computes it's dependencies"""
        sync = DiffLite(ChangeType.Added, self.to_absolute(filepath))
        self.all_syncs.append(sync)
        self.apply_diffs([sync])
        self.transaction_manager.check_limits()

    @contextmanager
    def session(self, sync_graph: bool = True, commit: bool = True, session_options: SessionOptions = SessionOptions()) -> Generator[None, None, None]:
        self.session_options = session_options
        self.transaction_manager.set_max_transactions(self.session_options.max_transactions)
        self.transaction_manager.reset_stopwatch(self.session_options.max_seconds)
        try:
            yield None
        except StopCodemodException as e:
            logger.info(f"{e}, committing transactions and resetting graph")
            raise
        finally:
            if commit:
                self.commit_transactions(sync_graph)

    def remove_directory(self, directory_path: PathLike, force: bool = False, cleanup: bool = True) -> None:
        """Removes a directory from the graph"""
        # Get the directory
        directory = self.get_directory(directory_path)

        # Check errors
        if directory is None:
            msg = f"Directory {directory_path} does not exist"
            raise ValueError(msg)
        if not force and len(directory.items) > 0:
            msg = f"Directory {directory_path} is not empty"
            raise ValueError(msg)

        # Remove the directory from the tree
        if str(directory_path) in self.directories:
            del self.directories[str(directory_path)]

        # Remove the directory from the parent
        if directory.parent is not None:
            directory.parent.remove_subdirectory(directory)
            # Cleanup
            if cleanup and len(directory.parent.items) == 0:
                self.remove_directory(directory.parent.path, cleanup=cleanup)

    ####################################################################################################################
    # EXTERNAL UTILS
    ####################################################################################################################

    _ts_declassify: TSDeclassify | None = None

    @property
    def ts_declassify(self) -> TSDeclassify:
        if self._ts_declassify is None:
            self._ts_declassify = TSDeclassify(self.repo_path, self.projects[0].base_path)
            self._ts_declassify.start()  # Install react-declassify
        return self._ts_declassify
