"""Codebase - main interface for Codemods to interact with the codebase"""

import codecs
import json
import os
import re
import tempfile
from collections.abc import Generator
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from typing import Generic, Literal, Unpack, overload

import plotly.graph_objects as go
import rich.repr
from git import Commit as GitCommit
from git import Diff
from git.remote import PushInfoList
from github.PullRequest import PullRequest
from networkx import Graph
from openai import OpenAI
from rich.console import Console
from typing_extensions import TypeVar, deprecated

from codegen.configs.models.codebase import CodebaseConfig, PinkMode
from codegen.configs.models.secrets import SecretsConfig
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import CheckoutResult, SetupOption
from codegen.git.schemas.repo_config import RepoConfig
from codegen.git.utils.pr_review import CodegenPR
from codegen.sdk._proxy import proxy_property
from codegen.sdk.ai.client import get_openai_client
from codegen.sdk.codebase.codebase_ai import generate_system_prompt, generate_tools
from codegen.sdk.codebase.codebase_context import (
    GLOBAL_FILE_IGNORE_LIST,
    CodebaseContext,
)
from codegen.sdk.codebase.config import ProjectConfig, SessionOptions
from codegen.sdk.codebase.diff_lite import DiffLite
from codegen.sdk.codebase.flagging.code_flag import CodeFlag
from codegen.sdk.codebase.flagging.enums import FlagKwargs
from codegen.sdk.codebase.flagging.group import Group
from codegen.sdk.codebase.io.io import IO
from codegen.sdk.codebase.progress.progress import Progress
from codegen.sdk.codebase.span import Span
from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.codeowner import CodeOwner
from codegen.sdk.core.detached_symbols.code_block import CodeBlock
from codegen.sdk.core.detached_symbols.parameter import Parameter
from codegen.sdk.core.directory import Directory
from codegen.sdk.core.export import Export
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.file import File, SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.interface import Interface
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.type_alias import TypeAlias
from codegen.sdk.enums import NodeType, SymbolType
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.extensions.utils import uncache_all
from codegen.sdk.output.constants import ANGULAR_STYLE
from codegen.sdk.python.assignment import PyAssignment
from codegen.sdk.python.class_definition import PyClass
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.detached_symbols.parameter import PyParameter
from codegen.sdk.python.file import PyFile
from codegen.sdk.python.function import PyFunction
from codegen.sdk.python.import_resolution import PyImport
from codegen.sdk.python.statements.import_statement import PyImportStatement
from codegen.sdk.python.symbol import PySymbol
from codegen.sdk.typescript.assignment import TSAssignment
from codegen.sdk.typescript.class_definition import TSClass
from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
from codegen.sdk.typescript.detached_symbols.parameter import TSParameter
from codegen.sdk.typescript.export import TSExport
from codegen.sdk.typescript.file import TSFile
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.import_resolution import TSImport
from codegen.sdk.typescript.interface import TSInterface
from codegen.sdk.typescript.statements.import_statement import TSImportStatement
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.sdk.typescript.type_alias import TSTypeAlias
from codegen.shared.decorators.docs import apidoc, noapidoc, py_noapidoc
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.exceptions.control_flow import MaxAIRequestsError
from codegen.shared.logging.get_logger import get_logger
from codegen.shared.performance.stopwatch_utils import stopwatch
from codegen.visualizations.visualization_manager import VisualizationManager

logger = get_logger(__name__)
MAX_LINES = 10000  # Maximum number of lines of text allowed to be logged


TSourceFile = TypeVar("TSourceFile", bound="SourceFile", default=SourceFile)
TDirectory = TypeVar("TDirectory", bound="Directory", default=Directory)
TSymbol = TypeVar("TSymbol", bound="Symbol", default=Symbol)
TClass = TypeVar("TClass", bound="Class", default=Class)
TFunction = TypeVar("TFunction", bound="Function", default=Function)
TImport = TypeVar("TImport", bound="Import", default=Import)
TGlobalVar = TypeVar("TGlobalVar", bound="Assignment", default=Assignment)
TInterface = TypeVar("TInterface", bound="Interface", default=Interface)
TTypeAlias = TypeVar("TTypeAlias", bound="TypeAlias", default=TypeAlias)
TParameter = TypeVar("TParameter", bound="Parameter", default=Parameter)
TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock", default=CodeBlock)
TExport = TypeVar("TExport", bound="Export", default=Export)
TSGlobalVar = TypeVar("TSGlobalVar", bound="Assignment", default=Assignment)
PyGlobalVar = TypeVar("PyGlobalVar", bound="Assignment", default=Assignment)
TSDirectory = Directory[TSFile, TSSymbol, TSImportStatement, TSGlobalVar, TSClass, TSFunction, TSImport]
PyDirectory = Directory[PyFile, PySymbol, PyImportStatement, PyGlobalVar, PyClass, PyFunction, PyImport]


@apidoc
class Codebase(
    Generic[
        TSourceFile,
        TDirectory,
        TSymbol,
        TClass,
        TFunction,
        TImport,
        TGlobalVar,
        TInterface,
        TTypeAlias,
        TParameter,
        TCodeBlock,
    ]
):
    """This class provides the main entrypoint for most programs to analyzing and manipulating codebases.

    Attributes:
        viz: Manages visualization of the codebase graph.
        repo_path: The path to the repository.
        console: Manages console output for the codebase.
    """

    _op: RepoOperator
    viz: VisualizationManager
    repo_path: Path
    console: Console

    @overload
    def __init__(
        self,
        repo_path: None = None,
        *,
        language: None = None,
        projects: list[ProjectConfig] | ProjectConfig,
        config: CodebaseConfig | None = None,
        secrets: SecretsConfig | None = None,
        io: IO | None = None,
        progress: Progress | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        repo_path: str,
        *,
        language: Literal["python", "typescript"] | ProgrammingLanguage | None = None,
        projects: None = None,
        config: CodebaseConfig | None = None,
        secrets: SecretsConfig | None = None,
        io: IO | None = None,
        progress: Progress | None = None,
    ) -> None: ...

    def __init__(
        self,
        repo_path: str | None = None,
        *,
        language: Literal["python", "typescript"] | ProgrammingLanguage | None = None,
        projects: list[ProjectConfig] | ProjectConfig | None = None,
        config: CodebaseConfig | None = None,
        secrets: SecretsConfig | None = None,
        io: IO | None = None,
        progress: Progress | None = None,
    ) -> None:
        # Sanity check inputs
        if repo_path is not None and projects is not None:
            msg = "Cannot specify both repo_path and projects"
            raise ValueError(msg)

        if repo_path is None and projects is None:
            msg = "Must specify either repo_path or projects"
            raise ValueError(msg)

        if projects is not None and language is not None:
            msg = "Cannot specify both projects and language. Use ProjectConfig.from_path() to create projects with a custom language."
            raise ValueError(msg)

        # If projects is a single ProjectConfig, convert it to a list
        if isinstance(projects, ProjectConfig):
            projects = [projects]

        # Initialize project with repo_path if projects is None
        if repo_path is not None:
            main_project = ProjectConfig.from_path(
                repo_path,
                programming_language=ProgrammingLanguage(language.upper()) if language else None,
            )
            projects = [main_project]
        else:
            main_project = projects[0]

        # Initialize codebase
        self._op = main_project.repo_operator
        self.viz = VisualizationManager(op=self._op)
        self.repo_path = Path(self._op.repo_path)
        self.ctx = CodebaseContext(projects, config=config, secrets=secrets, io=io, progress=progress)
        self.console = Console(record=True, soft_wrap=True)
        if self.ctx.config.use_pink != PinkMode.OFF:
            import codegen_sdk_pink

            self._pink_codebase = codegen_sdk_pink.Codebase(self.repo_path)

    @noapidoc
    def __str__(self) -> str:
        return f"<Codebase(name={self.name}, language={self.language}, path={self.repo_path})>"

    @noapidoc
    def __repr__(self):
        return str(self)

    def __rich_repr__(self) -> rich.repr.Result:
        yield "repo", self.ctx.repo_name
        yield "nodes", len(self.ctx.nodes)
        yield "edges", len(self.ctx.edges)

    __rich_repr__.angular = ANGULAR_STYLE

    @property
    @deprecated("Please do not use the local repo operator directly")
    @noapidoc
    def op(self) -> RepoOperator:
        return self._op

    @property
    def github(self) -> RepoOperator:
        """Access GitHub operations through the repo operator.

        This property provides access to GitHub operations like creating PRs,
        working with branches, commenting on PRs, etc. The implementation is built
        on top of PyGitHub (python-github library) and provides a simplified interface
        for common GitHub operations.

        Returns:
            RepoOperator: The repo operator instance that handles GitHub operations.
        """
        return self._op

    ####################################################################################################################
    # SIMPLE META
    ####################################################################################################################

    @property
    def name(self) -> str:
        """The name of the repository."""
        return self.ctx.repo_name

    @property
    def language(self) -> ProgrammingLanguage:
        """The programming language of the repository."""
        return self.ctx.programming_language

    ####################################################################################################################
    # NODES
    ####################################################################################################################

    @noapidoc
    def _symbols(self, symbol_type: SymbolType | None = None) -> list[TSymbol | TClass | TFunction | TGlobalVar]:
        matches: list[Symbol] = self.ctx.get_nodes(NodeType.SYMBOL)
        return [x for x in matches if x.is_top_level and (symbol_type is None or x.symbol_type == symbol_type)]

    # =====[ Node Types ]=====
    @overload
    def files(self, *, extensions: list[str]) -> list[File]: ...
    @overload
    def files(self, *, extensions: Literal["*"]) -> list[File]: ...
    @overload
    def files(self, *, extensions: None = ...) -> list[TSourceFile]: ...
    @proxy_property
    def files(self, *, extensions: list[str] | Literal["*"] | None = None) -> list[TSourceFile] | list[File]:
        """A list property that returns all files in the codebase.

        By default, this only returns source files. Setting `extensions='*'` will return all files in the codebase, and
        `extensions=[...]` will return all files with the specified extensions.

        For Python and Typescript repos WITH file parsing enabled,
        `extensions='*'` is REQUIRED for listing all non source code files.
        Or else, codebase.files will ONLY return source files (e.g. .py, .ts).

        For repos with file parsing disabled or repos with other languages, this will return all files in the codebase.

        Returns all Files in the codebase, sorted alphabetically. For Python codebases, returns PyFiles (python files).
        For Typescript codebases, returns TSFiles (typescript files).

        Returns:
            list[TSourceFile]: A sorted list of source files in the codebase.
        """
        if self.ctx.config.use_pink == PinkMode.ALL_FILES:
            return self._pink_codebase.files
        if extensions is None and len(self.ctx.get_nodes(NodeType.FILE)) > 0:
            # If extensions is None AND there is at least one file in the codebase (This checks for unsupported languages or parse-off repos),
            # Return all source files
            files = self.ctx.get_nodes(NodeType.FILE)
        elif isinstance(extensions, str) and extensions != "*":
            msg = "extensions must be a list of extensions or '*'"
            raise ValueError(msg)
        else:
            files = []
            # Get all files with the specified extensions
            for filepath, _ in self._op.iter_files(
                extensions=None if extensions == "*" else extensions,
                ignore_list=GLOBAL_FILE_IGNORE_LIST,
            ):
                files.append(self.get_file(filepath, optional=False))
        # Sort files alphabetically
        return sort_editables(files, alphabetical=True, dedupe=False)

    @cached_property
    def codeowners(self) -> list["CodeOwner[TSourceFile]"]:
        """List all CodeOnwers in the codebase.

        Returns:
            list[CodeOwners]: A list of CodeOwners objects in the codebase.
        """
        if self.ctx.codeowners_parser is None:
            return []
        return CodeOwner.from_parser(
            self.ctx.codeowners_parser,
            lambda *args, **kwargs: self.files(*args, **kwargs),
        )

    @property
    def directories(self) -> list[TDirectory]:
        """List all directories in the codebase.

        Returns a list of all Directory objects present in the codebase. Each Directory object represents a directory in the codebase.
        This property is used to access and navigate the directory structure of the codebase.

        Returns:
            list[TDirectory]: A list of Directory objects in the codebase.
        """
        return list(self.ctx.directories.values())

    @property
    def imports(self) -> list[TImport]:
        """Returns a list of all Import nodes in the codebase.

        Retrieves all Import nodes from the codebase graph. These imports represent all import statements across all files in the codebase,
        including imports from both internal modules and external packages.

        Args:
            None

        Returns:
            list[TImport]: A list of Import nodes representing all imports in the codebase.
            TImport can be PyImport for Python codebases or TSImport for TypeScript codebases.
        """
        return self.ctx.get_nodes(NodeType.IMPORT)

    @property
    @py_noapidoc
    def exports(self: "TSCodebaseType") -> list[TSExport]:
        """Returns a list of all Export nodes in the codebase.

        Retrieves all Export nodes from the codebase graph. These exports represent all export statements across all files in the codebase,
        including exports from both internal modules and external packages. This is a TypeScript-only codebase property.

        Args:
            None

        Returns:
            list[TSExport]: A list of Export nodes representing all exports in the codebase.
            TExport can only be a  TSExport for TypeScript codebases.

        """
        if self.language == ProgrammingLanguage.PYTHON:
            msg = "Exports are not supported for Python codebases since Python does not have an export mechanism."
            raise NotImplementedError(msg)

        return self.ctx.get_nodes(NodeType.EXPORT)

    @property
    def external_modules(self) -> list[ExternalModule]:
        """Returns a list of all external modules in the codebase.

        An external module represents a dependency that is imported but not defined within the codebase itself (e.g. third-party packages like 'requests' or 'numpy').

        Returns:
            list[ExternalModule]: List of external module nodes from the codebase graph.
        """
        return self.ctx.get_nodes(NodeType.EXTERNAL)

    @property
    def symbols(self) -> list[TSymbol]:
        """List of all top-level Symbols (Classes, Functions, etc.) in the codebase. Excludes Class
        methods.

        Returns:
            list[TSymbol]: A list of Symbol objects of all top-level symbols in the codebase. Includes classes, functions, and global variables defined at the module level, excludes methods.
        """
        return self._symbols()

    @property
    def classes(self) -> list[TClass]:
        """List of all Classes in the codebase.

        Returns a sorted list of all Class nodes in the codebase. Class nodes represent class definitions in source files.
        Only includes top-level classes, not inner/nested classes.

        Returns:
            list[TClass]: A sorted list of all Class nodes in the codebase.
        """
        return sort_editables(self._symbols(symbol_type=SymbolType.Class), dedupe=False)

    @property
    def functions(self) -> list[TFunction]:
        """List of all Functions in the codebase.

        Returns a sorted list of all top-level Function objects in the codebase, excluding class methods.

        Returns:
            list[TFunction]: A list of Function objects representing all functions in the codebase, sorted alphabetically.
        """
        return sort_editables(self._symbols(symbol_type=SymbolType.Function), dedupe=False)

    @property
    def global_vars(self) -> list[TGlobalVar]:
        """List of all GlobalVars in the codebase.

        A GlobalVar represents a global variable assignment in the source code. These are variables defined at the module level.

        Returns:
            list[TGlobalVar]: A list of all global variable assignments in the codebase.
        """
        return self._symbols(symbol_type=SymbolType.GlobalVar)

    @property
    def interfaces(self) -> list[TInterface]:
        """Retrieves all interfaces in the codebase.

        Returns a list of all Interface symbols defined at the top-level of source files in the codebase.
        This property is only applicable for TypeScript codebases and will return an empty list for Python codebases.

        Returns:
            list[TInterface]: A list of Interface objects defined in the codebase's source files.
        """
        return self._symbols(symbol_type=SymbolType.Interface)

    @property
    def types(self) -> list[TTypeAlias]:
        """List of all Types in the codebase (Typescript only).

        Returns a list of all type aliases defined at the top level in the codebase. This method is only applicable
        for TypeScript codebases.

        Returns:
            list[TTypeAlias]: A list of all type aliases defined in the codebase.
        """
        return self._symbols(symbol_type=SymbolType.Type)

    ####################################################################################################################
    # EDGES
    ####################################################################################################################
    # TODO - no utilities needed here at the moment, but revisit

    ####################################################################################################################
    # EXTERNAL API
    ####################################################################################################################

    def create_file(self, filepath: str, content: str = "", sync: bool = True) -> TSourceFile:
        """Creates a new file in the codebase with specified content.

        Args:
            filepath (str): The path where the file should be created.
            content (str): The content of the file to be created. Defaults to empty string.
            sync (bool): Whether to sync the graph after creating the file. Defaults to True.

        Returns:
            File: The newly created file object.

        Raises:
            ValueError: If the provided content cannot be parsed according to the file extension.
        """
        # Check if file already exists
        # NOTE: This check is also important to ensure the filepath is valid within the repo!
        if self.has_file(filepath):
            logger.warning(f"File {filepath} already exists in codebase. Overwriting...")

        file_exts = self.ctx.extensions
        # Create file as source file if it has a registered extension
        if any(filepath.endswith(ext) for ext in file_exts) and not self.ctx.config.disable_file_parse:
            file_cls = self.ctx.node_classes.file_cls
            file = file_cls.from_content(filepath, content, self.ctx, sync=sync)
            if file is None:
                msg = f"Failed to parse file with content {content}. Please make sure the content syntax is valid with respect to the filepath extension."
                raise ValueError(msg)
        else:
            # Create file as non-source file
            file = File.from_content(filepath, content, self.ctx, sync=False)

        # This is to make sure we keep track of this file for diff purposes
        uncache_all()
        return file

    def create_directory(self, dir_path: str, exist_ok: bool = False, parents: bool = False) -> None:
        """Creates a directory at the specified path.

        Args:
            dir_path (str): The path where the directory should be created.
            exist_ok (bool): If True, don't raise an error if the directory already exists. Defaults to False.
            parents (bool): If True, create any necessary parent directories. Defaults to False.

        Raises:
            FileExistsError: If the directory already exists and exist_ok is False.
        """
        # Check if directory already exists
        # NOTE: This check is also important to ensure the filepath is valid within the repo!
        if self.has_directory(dir_path):
            logger.warning(f"Directory {dir_path} already exists in codebase. Overwriting...")

        self.ctx.to_absolute(dir_path).mkdir(parents=parents, exist_ok=exist_ok)

    def has_file(self, filepath: str, ignore_case: bool = False) -> bool:
        """Determines if a file exists in the codebase.

        Args:
            filepath (str): The filepath to check for existence.
            ignore_case (bool): If True, ignore case when checking for file existence. Defaults to False.

        Returns:
            bool: True if the file exists in the codebase, False otherwise.
        """
        if self.ctx.config.use_pink == PinkMode.ALL_FILES:
            absolute_path = self.ctx.to_absolute(filepath)
            return self._pink_codebase.has_file(absolute_path)
        if self.ctx.config.use_pink == PinkMode.NON_SOURCE_FILES:
            if self._pink_codebase.has_file(filepath):
                return True
        return self.get_file(filepath, optional=True, ignore_case=ignore_case) is not None

    @overload
    def get_file(self, filepath: str, *, optional: Literal[False] = ..., ignore_case: bool = ...) -> TSourceFile: ...
    @overload
    def get_file(self, filepath: str, *, optional: Literal[True], ignore_case: bool = ...) -> TSourceFile | None: ...
    def get_file(self, filepath: str, *, optional: bool = False, ignore_case: bool = False) -> TSourceFile | None:
        """Retrieves a file from the codebase by its filepath.

        This method first attempts to find the file in the graph, then checks the filesystem if not found. Files can be either source files (e.g. .py, .ts) or binary files.

        Args:
            filepath (str): The path to the file, relative to the codebase root.
            optional (bool): If True, return None if file not found. If False, raise ValueError.
            ignore_case (bool): If True, ignore case when checking for file existence. Defaults to False.

        Returns:
            TSourceFile | None: The source file if found, None if optional=True and file not found.

        Raises:
            ValueError: If file not found and optional=False.
        """
        if self.ctx.config.use_pink == PinkMode.ALL_FILES:
            absolute_path = self.ctx.to_absolute(filepath)
            return self._pink_codebase.get_file(absolute_path)
        # Try to get the file from the graph first
        file = self.ctx.get_file(filepath, ignore_case=ignore_case)
        if file is not None:
            return file

        # If the file is not in the graph, check the filesystem
        absolute_path = self.ctx.to_absolute(filepath)
        if self.ctx.io.file_exists(absolute_path):
            if self.ctx.config.use_pink != PinkMode.OFF:
                if file := self._pink_codebase.get_file(absolute_path):
                    return file
            return self.ctx._get_raw_file_from_path(absolute_path)
        # If the file is not in the graph, check the filesystem
        if absolute_path.parent.exists():
            for file in absolute_path.parent.iterdir():
                if ignore_case and str(absolute_path).lower() == str(file).lower():
                    return self.ctx._get_raw_file_from_path(file)
                elif not ignore_case and str(absolute_path) == str(file):
                    return self.ctx._get_raw_file_from_path(file)

        # If we get here, the file is not found
        if not optional:
            msg = f"File {filepath} not found in codebase. Use optional=True to return None instead."
            raise ValueError(msg)
        return None

    def has_directory(self, dir_path: str, ignore_case: bool = False) -> bool:
        """Returns a boolean indicating if a directory exists in the codebase.

        Checks if a directory exists at the specified path within the codebase.

        Args:
            dir_path (str): The path to the directory to check for, relative to the codebase root.

        Returns:
            bool: True if the directory exists in the codebase, False otherwise.
        """
        return self.get_directory(dir_path, optional=True, ignore_case=ignore_case) is not None

    def get_directory(self, dir_path: str, optional: bool = False, ignore_case: bool = False) -> TDirectory | None:
        """Returns Directory by `dir_path`, or full path to the directory from codebase root.

        Args:
            dir_path (str): The path to the directory to retrieve.
            optional (bool): If True, return None when directory is not found. If False, raise ValueError.

        Returns:
            TDirectory | None: The Directory object if found, None if optional=True and directory not found.

        Raises:
            ValueError: If directory not found and optional=False.
        """
        # Sanitize the path
        dir_path = os.path.normpath(dir_path)
        dir_path = "" if dir_path == "." else dir_path
        directory = self.ctx.get_directory(self.ctx.to_absolute(dir_path), ignore_case=ignore_case)
        if directory is None and not optional:
            msg = f"Directory {dir_path} not found in codebase. Use optional=True to return None instead."
            raise ValueError(msg)
        return directory

    def has_symbol(self, symbol_name: str) -> bool:
        """Returns whether a symbol exists in the codebase.

        This method checks if a symbol with the given name exists in the codebase.

        Args:
            symbol_name (str): The name of the symbol to look for.

        Returns:
            bool: True if a symbol with the given name exists in the codebase, False otherwise.
        """
        return any([x.name == symbol_name for x in self.symbols])

    def get_symbol(self, symbol_name: str, optional: bool = False) -> TSymbol | None:
        """Returns a Symbol by name from the codebase.

        Returns the first Symbol that matches the given name. If multiple symbols are found with the same name, raises a ValueError.
        If no symbol is found, returns None if optional is True, otherwise raises a ValueError.

        Args:
            symbol_name (str): The name of the symbol to find.
            optional (bool): If True, returns None when symbol is not found. If False, raises ValueError. Defaults to False.

        Returns:
            TSymbol | None: The matched Symbol if found, None if not found and optional=True.

        Raises:
            ValueError: If multiple symbols are found with the same name, or if no symbol is found and optional=False.
        """
        symbols = self.get_symbols(symbol_name)
        if len(symbols) == 0:
            if not optional:
                msg = f"Symbol {symbol_name} not found in codebase. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(symbols) > 1:
            msg = f"Symbol {symbol_name} is ambiguous in codebase - more than one instance"
            raise ValueError(msg)
        return symbols[0]

    def get_symbols(self, symbol_name: str) -> list[TSymbol]:
        """Retrieves all symbols in the codebase that match the given symbol name.

        This method is used when there may be multiple symbols with the same name, in which case get_symbol() would raise a ValueError.

        Args:
            symbol_name (str): The name of the symbols to retrieve.

        Returns:
            list[TSymbol]: A list of Symbol objects that match the given name, sorted alphabetically.

        Note:
            When a unique symbol is required, use get_symbol() instead. It will raise ValueError if multiple symbols are found.
        """
        return sort_editables(x for x in self.symbols if x.name == symbol_name)

    def get_class(self, class_name: str, optional: bool = False) -> TClass | None:
        """Returns a class that matches the given name.

        Args:
            class_name (str): The name of the class to find.
            optional (bool): If True, return None when class is not found instead of raising ValueError. Defaults to False.

        Returns:
            TClass | None: The class with the given name, or None if optional=True and class not found.

        Raises:
            ValueError: If the class is not found and optional=False, or if multiple classes with the same name exist.
        """
        matches = [c for c in self.classes if c.name == class_name]
        if len(matches) == 0:
            if not optional:
                msg = f"Class {class_name} not found in codebase. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(matches) > 1:
            msg = f"Class {class_name} is ambiguous in codebase - more than one instance"
            raise ValueError(msg)
        return matches[0]

    def get_function(self, function_name: str, optional: bool = False) -> TFunction | None:
        """Retrieves a function from the codebase by its name.

        This method searches through all functions in the codebase to find one matching the given name.
        If multiple functions with the same name exist, a ValueError is raised.

        Args:
            function_name (str): The name of the function to retrieve.
            optional (bool): If True, returns None when function is not found instead of raising ValueError.
                            Defaults to False.

        Returns:
            TFunction | None: The matching function if found. If optional=True and no match is found,
                             returns None.

        Raises:
            ValueError: If function is not found and optional=False, or if multiple matching functions exist.
        """
        matches = [f for f in self.functions if f.name == function_name]
        if len(matches) == 0:
            if not optional:
                msg = f"Function {function_name} not found in codebase. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(matches) > 1:
            msg = f"Function {function_name} is ambiguous in codebase - more than one instance"
            raise ValueError(msg)
        return matches[0]

    @noapidoc
    @staticmethod
    def _remove_extension(filename: str) -> str:
        """Removes the trailing extension from the filename if it appears at the end,
        e.g. filename.ext -> filename
        """
        return re.sub(r"\.[^.]+$", "", filename)

    def get_relative_path(self, from_file: str, to_file: str) -> str:
        """Calculates a relative path from one file to another, removing the extension from the target file.

        This method splits both `from_file` and `to_file` by forward slashes, finds their common path prefix,
        and determines how many directories to traverse upward from `from_file` before moving into the
        remaining directories of `to_file` (with its extension removed).

        Args:
            from_file (str): The file path from which the relative path will be computed.
            to_file (str): The file path (whose extension will be removed) to which the relative path will be computed.

        Returns:
            str: The relative path from `from_file` to `to_file` (with the extension removed from `to_file`).
        """
        # Remove extension from the target file
        to_file = self._remove_extension(to_file)

        from_parts = from_file.split("/")
        to_parts = to_file.split("/")

        # Find common prefix
        i = 0
        while i < len(from_parts) - 1 and i < len(to_parts) and from_parts[i] == to_parts[i]:
            i += 1

        # Number of '../' we need
        up_levels = len(from_parts) - i - 1

        # Construct relative path
        relative_path = ("../" * up_levels) + "/".join(to_parts[i:])

        return relative_path

    ####################################################################################################################
    # State/Git
    ####################################################################################################################

    def git_commit(self, message: str, *, verify: bool = False, exclude_paths: list[str] | None = None) -> GitCommit | None:
        """Stages + commits all changes to the codebase and git.

        Args:
            message (str): The commit message
            verify (bool): Whether to verify the commit before committing. Defaults to False.

        Returns:
            GitCommit | None: The commit object if changes were committed, None otherwise.
        """
        self.ctx.commit_transactions(sync_graph=False)
        if self._op.stage_and_commit_all_changes(message, verify, exclude_paths):
            logger.info(f"Commited repository to {self._op.head_commit} on {self._op.get_active_branch_or_commit()}")
            return self._op.head_commit
        else:
            logger.info("No changes to commit")
        return None

    def commit(self, sync_graph: bool = True) -> None:
        """Commits all staged changes to the codebase graph and synchronizes the graph with the filesystem if specified.

        This method must be called when multiple overlapping edits are made on a single entity to ensure proper tracking of changes.
        For example, when renaming a symbol and then moving it to a different file, commit must be called between these operations.

        Args:
            sync_graph (bool): Whether to synchronize the graph after committing changes. Defaults to True.

        Returns:
            None
        """
        self.ctx.commit_transactions(sync_graph=sync_graph and self.ctx.config.sync_enabled)

    @noapidoc
    def git_push(self, *args, **kwargs) -> PushInfoList:
        """Git push."""
        return self._op.push_changes(*args, **kwargs)

    @property
    def default_branch(self) -> str:
        """The default branch of this repository.

        Returns the name of the default branch (e.g. 'main' or 'master') for the current repository.

        Returns:
            str: The name of the default branch.
        """
        return self._op.default_branch

    @property
    def current_commit(self) -> GitCommit | None:
        """Returns the current Git commit that is checked out in the repository.

        Args:
            None

        Returns:
            GitCommit | None: The currently checked out Git commit object, or None if no commit is checked out.
        """
        return self._op.git_cli.head.commit

    @stopwatch
    def reset(self, git_reset: bool = False) -> None:
        """Resets the codebase by:
        - Discarding any staged/unstaged changes
        - Resetting stop codemod limits: (max seconds, max transactions, max AI requests)
        - Clearing logs
        - Clearing pending transactions + pending files
        - Syncing graph to synced_commit

        This will ignore changes to:
        - .codegen directory (for codemod development)
        - .ipynb files (Jupyter notebooks, where you are likely developing)
        """
        logger.info("Resetting codebase ...")
        if git_reset:
            self._op.discard_changes()  # Discard any changes made to the raw file state
        self._num_ai_requests = 0
        self.reset_logs()
        self.ctx.undo_applied_diffs()

    def checkout(
        self,
        *,
        commit: str | GitCommit | None = None,
        branch: str | None = None,
        create_if_missing: bool = False,
        remote: bool = False,
    ) -> CheckoutResult:
        """Checks out a git branch or commit and syncs the codebase graph to the new state.

        This method discards any pending changes, performs a git checkout of the specified branch or commit,
        and then syncs the codebase graph to reflect the new state.

        Args:
            commit (str | GitCommit | None): Hash or GitCommit object to checkout. Cannot be used with branch.
            branch (str | None): Name of branch to checkout. Cannot be used with commit.
            create_if_missing (bool): If True, creates the branch if it doesn't exist. Defaults to False.
            remote (bool): If True, attempts to pull from remote when checking out branch. Defaults to False.

        Returns:
            CheckoutResult: The result of the checkout operation.

        Raises:
            AssertionError: If neither commit nor branch is specified, or if both are specified.
        """
        self.reset()
        if commit is None:
            assert branch is not None, "Commit or branch must be specified"
            logger.info(f"Checking out branch {branch}")
            result = self._op.checkout_branch(branch, create_if_missing=create_if_missing, remote=remote)
        else:
            assert branch is None, "Cannot specify branch and commit"
            logger.info(f"Checking out commit {commit}")
            result = self._op.checkout_commit(commit_hash=commit)
        if result == CheckoutResult.SUCCESS:
            logger.info(f"Checked out {branch or commit}")
            self.sync_to_commit(self._op.head_commit)
        elif result == CheckoutResult.NOT_FOUND:
            logger.info(f"Could not find branch {branch or commit}")

        return result

    @noapidoc
    def sync_to_commit(self, target_commit: GitCommit) -> None:
        """Updates the current base to a new commit."""
        origin_commit = self.ctx.synced_commit
        if origin_commit.hexsha == target_commit.hexsha:
            logger.info(f"Codebase is already synced to {target_commit.hexsha}. Skipping sync_to_commit.")
            return
        if not self.ctx.config.sync_enabled:
            logger.info(f"Syncing codebase is disabled for repo {self._op.repo_name}. Skipping sync_to_commit.")
            return

        logger.info(f"Syncing {self._op.repo_name} to {target_commit.hexsha}")
        diff_index = origin_commit.diff(target_commit)
        diff_lites = []
        for diff in diff_index:
            diff_lites.append(DiffLite.from_git_diff(diff))
        self.ctx.apply_diffs(diff_lites)
        self.ctx.save_commit(target_commit)

    @noapidoc
    def get_diffs(self, base: str | None = None) -> list[Diff]:
        """Get all changed files."""
        if base is None:
            return self._op.get_diffs(self._op.head_commit)
        return self._op.get_diffs(base)

    @noapidoc
    def get_diff(self, base: str | None = None, stage_files: bool = False) -> str:
        """Produce a single git diff for all files."""
        if stage_files:
            self._op.git_cli.git.add(A=True)  # add all changes to the index so untracked files are included in the diff
        if base is None:
            diff = self._op.git_cli.git.diff("HEAD", patch=True, full_index=True)
            return diff
        return self._op.git_cli.git.diff(base, patch=True, full_index=True)

    @noapidoc
    def clean_repo(self):
        """Cleaning a codebase repo by:
        1. Deleting all branches except the checked out one
        2. Deleting all remotes except origin

        NOTE: doesn't discard changes b/c this should be handled by self.reset
        NOTE: doesn't checkout onto the default branch b/c this should be handled by self.checkout
        """
        logger.info(f"Cleaning codebase repo at {self.repo_path} ...")
        self._op.clean_remotes()
        self._op.clean_branches()

    @noapidoc
    def stash_changes(self):
        """Stash all changes in the codebase."""
        self._op.stash_push()

    @noapidoc
    def restore_stashed_changes(self):
        """Restore the most recent stash in the codebase."""
        self._op.stash_pop()

    ####################################################################################################################
    # GITHUB
    ####################################################################################################################

    def create_pr(self, title: str, body: str) -> PullRequest:
        """Creates a pull request from the current branch to the repository's default branch.

        This method will:
        1. Stage and commit any pending changes with the PR title as the commit message
        2. Push the current branch to the remote repository
        3. Create a pull request targeting the default branch

        Args:
            title (str): The title for the pull request
            body (str): The description/body text for the pull request

        Returns:
            PullRequest: The created GitHub pull request object

        Raises:
            ValueError: If attempting to create a PR while in a detached HEAD state
            ValueError: If the current branch is the default branch
        """
        if self._op.git_cli.head.is_detached:
            msg = "Cannot make a PR from a detached HEAD"
            raise ValueError(msg)
        if self._op.git_cli.active_branch.name == self._op.default_branch:
            msg = "Cannot make a PR from the default branch"
            raise ValueError(msg)
        self._op.stage_and_commit_all_changes(message=title)
        self._op.push_changes()
        return self._op.remote_git_repo.create_pull(
            head_branch_name=self._op.git_cli.active_branch.name,
            base_branch_name=self._op.default_branch,
            title=title,
            body=body,
        )

    ####################################################################################################################
    # GRAPH VISUALIZATION
    ####################################################################################################################

    def visualize(self, G: Graph | go.Figure, root: Editable | str | int | None = None) -> None:
        """Visualizes a NetworkX graph or Plotly figure.

        Creates a visualization of the provided graph using GraphViz. This is useful for visualizing dependency graphs, call graphs,
        directory structures, or other graph-based representations of code relationships.

        Args:
            G (Graph | go.Figure): A NetworkX graph or Plotly figure to visualize
            root (Editable | str | int | None): The root node to visualize around. When specified, the visualization will be centered on this node. Defaults to None.

        Returns:
            None
        """
        self.viz.write_graphviz_data(G=G, root=root)

    ####################################################################################################################
    # FLAGGING
    ####################################################################################################################

    @noapidoc
    def flags(self) -> list[CodeFlag]:
        """Returns all collected code flags in find mode.

        Returns:
            list[CodeFlag]: A list of all flags in the codebase.
        """
        return self.ctx.flags._flags

    @noapidoc
    def flag_instance(
        self,
        symbol: TSymbol | None = None,
        **kwargs: Unpack[FlagKwargs],
    ) -> CodeFlag:
        """Flags a symbol, file or import to enable enhanced tracking of changes and splitting into
        smaller PRs.

        This method should be called once per flaggable entity and should be called before any edits are made to the entity.
        Flags enable tracking of changes and can be used for various purposes like generating pull requests or applying changes selectively.

        Args:
            symbol (TSymbol | None): The symbol to flag. Can be None if just flagging a message.
            **kwargs: Arguments used to construct the flag
        Returns:
            CodeFlag: A flag object representing the flagged entity.
        """
        return self.ctx.flags.flag_instance(symbol, **kwargs)

    def should_fix(self, flag: CodeFlag) -> bool:
        """Returns True if the flag should be fixed based on the current mode and active group.

        Used to filter out flags that are not in the active group and determine if the flag should be processed or ignored.

        Args:
            flag (CodeFlag): The code flag to check.

        Returns:
            bool: True if the flag should be fixed, False if it should be ignored.
            Returns False in find mode.
            Returns True if no active group is set.
            Returns True if the flag's hash exists in the active group hashes.
        """
        return self.ctx.flags.should_fix(flag)

    @noapidoc
    def set_find_mode(self, find_mode: bool) -> None:
        self.ctx.flags.set_find_mode(find_mode)

    @noapidoc
    def set_active_group(self, group: Group) -> None:
        """Will only fix these flags."""
        # TODO - flesh this out more with Group datatype and GroupBy
        self.ctx.flags.set_active_group(group)

    ####################################################################################################################
    # LOGGING
    ####################################################################################################################

    _logs = []

    def __is_markup_loggable__(self, arg) -> bool:
        return isinstance(arg, Editable)

    @noapidoc
    def log(self, *args) -> None:
        """Logs a message as a string.

        At the end, we will save a tail of these logs on the CodemodRun
        """
        self.ctx.transaction_manager.check_max_preview_time()
        if self.console.export_text(clear=False).count("\n") >= MAX_LINES:
            return  # if max lines has been reached, skip logging
        for arg in args:
            if self.__is_markup_loggable__(arg):
                fullName = arg.get_name() if isinstance(arg, HasName) and arg.get_name() else ""
                doc_lang = arg._api_doc_lang if hasattr(arg, "_api_doc_lang") else None
                class_name = arg.__class__.__name__
                link = f"::docs/codebase-sdk/{doc_lang}/{class_name}" if doc_lang is not None else ""
                self.console.print(f"{class_name}::{fullName}{link}", markup=True, soft_wrap=True)
        args = [arg for arg in args if not self.__is_markup_loggable__(arg)]
        if args:
            self.console.print(*args, markup=True, soft_wrap=True)

    @noapidoc
    def reset_logs(self) -> None:
        """Resets the logs."""
        self.console.clear()

    @noapidoc
    def get_finalized_logs(self) -> str:
        """Returns the logs as a string, truncating if necessary."""
        return self.console.export_text()

    ####################################################################################################################
    # INTERNAL UTILS
    ####################################################################################################################

    @contextmanager
    @noapidoc
    def session(
        self,
        sync_graph: bool = True,
        commit: bool = True,
        session_options: SessionOptions = SessionOptions(),
    ) -> Generator[None, None, None]:
        with self.ctx.session(sync_graph=sync_graph, commit=commit, session_options=session_options):
            yield None

    @noapidoc
    def _enable_experimental_language_engine(
        self,
        async_start: bool = False,
        install_deps: bool = False,
        use_v8: bool = False,
    ) -> None:
        """Debug option to enable experimental language engine for the current codebase."""
        if install_deps and not self.ctx.language_engine:
            from codegen.sdk.core.external.dependency_manager import (
                get_dependency_manager,
            )

            logger.info("Cold installing dependencies...")
            logger.info("This may take a while for large repos...")
            self.ctx.dependency_manager = get_dependency_manager(self.ctx.projects[0].programming_language, self.ctx, enabled=True)
            self.ctx.dependency_manager.start(async_start=False)
            # Wait for the dependency manager to be ready
            self.ctx.dependency_manager.wait_until_ready(ignore_error=False)
            logger.info("Dependencies ready")
        if not self.ctx.language_engine:
            from codegen.sdk.core.external.language_engine import get_language_engine

            logger.info("Cold starting language engine...")
            logger.info("This may take a while for large repos...")
            self.ctx.language_engine = get_language_engine(
                self.ctx.projects[0].programming_language,
                self.ctx,
                use_ts=True,
                use_v8=use_v8,
            )
            self.ctx.language_engine.start(async_start=async_start)
            # Wait for the language engine to be ready
            self.ctx.language_engine.wait_until_ready(ignore_error=False)
            logger.info("Language engine ready")

    ####################################################################################################################
    # AI
    ####################################################################################################################

    _ai_helper: OpenAI = None
    _num_ai_requests: int = 0

    @property
    @noapidoc
    def ai_client(self) -> OpenAI:
        """Enables calling AI/LLM APIs - re-export of the initialized `openai` module"""
        # Create a singleton AIHelper instance
        if self._ai_helper is None:
            if self.ctx.secrets.openai_api_key is None:
                msg = "OpenAI key is not set"
                raise ValueError(msg)

            self._ai_helper = get_openai_client(key=self.ctx.secrets.openai_api_key)
        return self._ai_helper

    def ai(
        self,
        prompt: str,
        target: Editable | None = None,
        context: Editable | list[Editable] | dict[str, Editable | list[Editable]] | None = None,
        model: str = "gpt-4o",
    ) -> str:
        """Generates a response from the AI based on the provided prompt, target, and context.

        A method that sends a prompt to the AI client along with optional target and context information to generate a response.
        Used for tasks like code generation, refactoring suggestions, and documentation improvements.

        Args:
            prompt (str): The text prompt to send to the AI.
            target (Editable | None): An optional editable object (like a function, class, etc.) that provides the main focus for the AI's response.
            context (Editable | list[Editable] | dict[str, Editable | list[Editable]] | None): Additional context to help inform the AI's response.
            model (str): The AI model to use for generating the response. Defaults to "gpt-4o".

        Returns:
            str: The generated response from the AI.

        Raises:
            MaxAIRequestsError: If the maximum number of allowed AI requests (default 150) has been exceeded.
        """
        # Check max transactions
        logger.info("Creating call to OpenAI...")
        self._num_ai_requests += 1
        if self.ctx.session_options.max_ai_requests is not None and self._num_ai_requests > self.ctx.session_options.max_ai_requests:
            logger.info(f"Max AI requests reached: {self.ctx.session_options.max_ai_requests}. Stopping codemod.")
            msg = f"Maximum number of AI requests reached: {self.ctx.session_options.max_ai_requests}"
            raise MaxAIRequestsError(msg, threshold=self.ctx.session_options.max_ai_requests)

        params = {
            "messages": [
                {"role": "system", "content": generate_system_prompt(target, context)},
                {"role": "user", "content": prompt},
            ],
            "model": model,
            "functions": generate_tools(),
            "temperature": 0,
        }
        if model.startswith("gpt"):
            params["tool_choice"] = "required"

        # Make the AI request
        response = self.ai_client.chat.completions.create(
            model=model,
            messages=params["messages"],
            tools=params["functions"],  # type: ignore
            temperature=params["temperature"],
            tool_choice=params["tool_choice"],
        )

        # Handle finish reasons
        # First check if there is a response
        if response.choices:
            # Check response reason
            choice = response.choices[0]
            if choice.finish_reason == "tool_calls" or choice.finish_reason == "function_call" or choice.finish_reason == "stop":
                # Check if there is a tool call
                if choice.message.tool_calls:
                    tool_call = choice.message.tool_calls[0]
                    response_answer = json.loads(tool_call.function.arguments)
                    if "answer" in response_answer:
                        response_answer = response_answer["answer"]
                    else:
                        msg = "No answer found in tool call. (tool_call.function.arguments does not contain answer)"
                        raise ValueError(msg)
                else:
                    msg = "No tool call found in AI response. (choice.message.tool_calls is empty)"
                    raise ValueError(msg)
            elif choice.finish_reason == "length":
                msg = "AI response too long / ran out of tokens. (choice.finish_reason == length)"
                raise ValueError(msg)
            elif choice.finish_reason == "content_filter":
                msg = "AI response was blocked by OpenAI's content filter. (choice.finish_reason == content_filter)"
                raise ValueError(msg)
            else:
                msg = f"Unknown finish reason from AI: {choice.finish_reason}"
                raise ValueError(msg)
        else:
            msg = "No response from AI Provider. (response.choices is empty)"
            raise ValueError(msg)

        # Agent sometimes fucks up and does \\\\n for some reason.
        response_answer = codecs.decode(response_answer, "unicode_escape")
        logger.info(f"OpenAI response: {response_answer}")
        return response_answer

    def set_ai_key(self, key: str) -> None:
        """Sets the OpenAI key for the current Codebase instance."""
        # Reset the AI client
        self._ai_helper = None

        # Set the AI key
        self.ctx.secrets.openai_api_key = key

    def find_by_span(self, span: Span) -> list[Editable]:
        """Finds editable objects that overlap with the given source code span.

        Searches for editable objects (like functions, classes, variables) within a file
        that overlap with the specified byte range span. Returns an empty list if no
        matching file is found.

        Args:
            span (Span): The span object containing the filepath and byte range to search within.

        Returns:
            list[Editable]: A list of Editable objects that overlap with the given span.
        """
        if file := self.get_file(span.filepath):
            return file.find_by_byte_range(span.range)
        return []

    def set_session_options(self, **kwargs: Unpack[SessionOptions]) -> None:
        """Sets the session options for the current codebase.

        This method updates the session options with the provided keyword arguments and
        configures the transaction manager accordingly. It sets the maximum number of
        transactions and resets the stopwatch based on the updated session options.

        Args:
        **kwargs: Keyword arguments representing the session options to update.
            - max_transactions (int, optional): The maximum number of transactions
              allowed in a session.
            - max_seconds (int, optional): The maximum duration in seconds for a session
              before it times out.
            - max_ai_requests (int, optional): The maximum number of AI requests
              allowed in a session.
        """
        self.ctx.session_options = self.ctx.session_options.model_copy(update=kwargs)
        self.ctx.transaction_manager.set_max_transactions(self.ctx.session_options.max_transactions)
        self.ctx.transaction_manager.reset_stopwatch(self.ctx.session_options.max_seconds)

    @classmethod
    def from_repo(
        cls,
        repo_full_name: str,
        *,
        tmp_dir: str | None = "/tmp/codegen",
        commit: str | None = None,
        language: Literal["python", "typescript"] | ProgrammingLanguage | None = None,
        config: CodebaseConfig | None = None,
        secrets: SecretsConfig | None = None,
        setup_option: SetupOption | None = None,
        full_history: bool = False,
    ) -> "Codebase":
        """Fetches a codebase from GitHub and returns a Codebase instance.

        Args:
            repo_name (str): The name of the repository in format "owner/repo"
            tmp_dir (Optional[str]): The directory to clone the repo into. Defaults to /tmp/codegen
            commit (Optional[str]): The specific commit hash to clone. Defaults to HEAD
            shallow (bool): Whether to do a shallow clone. Defaults to True
            language (Literal["python", "typescript"] | ProgrammingLanguage | None): The programming language of the repo. Defaults to None.
            config (CodebaseConfig): Configuration for the codebase. Defaults to pre-defined defaults if None.
            secrets (SecretsConfig): Configuration for the secrets. Defaults to empty values if None.

        Returns:
            Codebase: A Codebase instance initialized with the cloned repository
        """
        logger.info(f"Fetching codebase for {repo_full_name}")

        # Parse repo name
        if "/" not in repo_full_name:
            msg = "repo_name must be in format 'owner/repo'"
            raise ValueError(msg)
        owner, repo = repo_full_name.split("/")

        # Setup temp directory
        os.makedirs(tmp_dir, exist_ok=True)
        logger.info(f"Using directory: {tmp_dir}")

        # Setup repo path and URL
        repo_path = os.path.join(tmp_dir, repo)
        repo_url = f"https://github.com/{repo_full_name}.git"
        logger.info(f"Will clone {repo_url} to {repo_path}")
        access_token = secrets.github_token if secrets else None

        try:
            # Use RepoOperator to fetch the repository
            logger.info("Cloning repository...")
            if commit is None:
                repo_config = RepoConfig.from_repo_path(repo_path)
                repo_config.full_name = repo_full_name
                repo_operator = RepoOperator.create_from_repo(repo_path=repo_path, url=repo_url, access_token=access_token, full_history=full_history)
            else:
                # Ensure the operator can handle remote operations
                repo_operator = RepoOperator.create_from_commit(repo_path=repo_path, commit=commit, url=repo_url, full_name=repo_full_name, access_token=access_token)
            logger.info("Clone completed successfully")

            # Initialize and return codebase with proper context
            logger.info("Initializing Codebase...")
            project = ProjectConfig.from_repo_operator(
                repo_operator=repo_operator,
                programming_language=ProgrammingLanguage(language.upper()) if language else None,
            )
            codebase = Codebase(projects=[project], config=config, secrets=secrets)
            logger.info("Codebase initialization complete")
            return codebase
        except Exception as e:
            logger.exception(f"Failed to initialize codebase: {e}")
            raise

    @classmethod
    def from_string(
        cls,
        code: str,
        *,
        language: Literal["python", "typescript"] | ProgrammingLanguage,
    ) -> "Codebase":
        """Creates a Codebase instance from a string of code.

        Args:
            code: String containing code
            language: Language of the code. Defaults to Python.

        Returns:
            Codebase: A Codebase instance initialized with the provided code

        Example:
            >>> # Python code
            >>> code = "def add(a, b): return a + b"
            >>> codebase = Codebase.from_string(code, language="python")

            >>> # TypeScript code
            >>> code = "function add(a: number, b: number): number { return a + b; }"
            >>> codebase = Codebase.from_string(code, language="typescript")
        """
        if not language:
            msg = "missing required argument language"
            raise TypeError(msg)

        logger.info("Creating codebase from string")

        # Determine language and filename
        prog_lang = ProgrammingLanguage(language.upper()) if isinstance(language, str) else language
        filename = "test.ts" if prog_lang == ProgrammingLanguage.TYPESCRIPT else "test.py"

        # Create codebase using factory
        from codegen.sdk.codebase.factory.codebase_factory import CodebaseFactory

        files = {filename: code}

        with tempfile.TemporaryDirectory(prefix="codegen_") as tmp_dir:
            logger.info(f"Using directory: {tmp_dir}")
            codebase = CodebaseFactory.get_codebase_from_files(repo_path=tmp_dir, files=files, programming_language=prog_lang)
            logger.info("Codebase initialization complete")
            return codebase

    @classmethod
    def from_files(
        cls,
        files: dict[str, str],
        *,
        language: Literal["python", "typescript"] | ProgrammingLanguage | None = None,
    ) -> "Codebase":
        """Creates a Codebase instance from multiple files.

        Args:
            files: Dictionary mapping filenames to their content, e.g. {"main.py": "print('hello')"}
            language: Optional language override. If not provided, will be inferred from file extensions.
                     All files must have extensions matching the same language.

        Returns:
            Codebase: A Codebase instance initialized with the provided files

        Raises:
            ValueError: If file extensions don't match a single language or if explicitly provided
                       language doesn't match the extensions

        Example:
            >>> # Language inferred as Python
            >>> files = {"main.py": "print('hello')", "utils.py": "def add(a, b): return a + b"}
            >>> codebase = Codebase.from_files(files)

            >>> # Language inferred as TypeScript
            >>> files = {"index.ts": "console.log('hello')", "utils.tsx": "export const App = () => <div>Hello</div>"}
            >>> codebase = Codebase.from_files(files)
        """
        # Create codebase using factory
        from codegen.sdk.codebase.factory.codebase_factory import CodebaseFactory

        if not files:
            msg = "No files provided"
            raise ValueError(msg)

        logger.info("Creating codebase from files")

        prog_lang = ProgrammingLanguage.PYTHON  # Default language

        if files:
            py_extensions = {".py"}
            ts_extensions = {".ts", ".tsx", ".js", ".jsx"}

            extensions = {os.path.splitext(f)[1].lower() for f in files}
            inferred_lang = None

            # all check to ensure that the from_files method is being used for small testing purposes only.
            # If parsing an actual repo, it should not be used. Instead do Codebase("path/to/repo")
            if all(ext in py_extensions for ext in extensions):
                inferred_lang = ProgrammingLanguage.PYTHON
            elif all(ext in ts_extensions for ext in extensions):
                inferred_lang = ProgrammingLanguage.TYPESCRIPT
            else:
                msg = f"Cannot determine single language from extensions: {extensions}. Files must all be Python (.py) or TypeScript (.ts, .tsx, .js, .jsx)"
                raise ValueError(msg)

            if language is not None:
                explicit_lang = ProgrammingLanguage(language.upper()) if isinstance(language, str) else language
                if explicit_lang != inferred_lang:
                    msg = f"Provided language {explicit_lang} doesn't match inferred language {inferred_lang} from file extensions"
                    raise ValueError(msg)

            prog_lang = inferred_lang
        else:
            # Default to Python if no files provided
            prog_lang = ProgrammingLanguage.PYTHON if language is None else (ProgrammingLanguage(language.upper()) if isinstance(language, str) else language)

        logger.info(f"Using language: {prog_lang}")

        with tempfile.TemporaryDirectory(prefix="codegen_") as tmp_dir:
            logger.info(f"Using directory: {tmp_dir}")

            # Initialize git repo to avoid "not in a git repository" error
            import subprocess

            subprocess.run(["git", "init"], cwd=tmp_dir, check=True, capture_output=True)

            codebase = CodebaseFactory.get_codebase_from_files(repo_path=tmp_dir, files=files, programming_language=prog_lang)
            logger.info("Codebase initialization complete")
            return codebase

    def get_modified_symbols_in_pr(self, pr_id: int) -> tuple[str, dict[str, str], list[str]]:
        """Get all modified symbols in a pull request"""
        pr = self._op.get_pull_request(pr_id)
        cg_pr = CodegenPR(self._op, self, pr)
        patch = cg_pr.get_pr_diff()
        commit_sha = cg_pr.get_file_commit_shas()
        return patch, commit_sha, cg_pr.modified_symbols

    def create_pr_comment(self, pr_number: int, body: str) -> None:
        """Create a comment on a pull request"""
        return self._op.create_pr_comment(pr_number, body)

    def create_pr_review_comment(
        self,
        pr_number: int,
        body: str,
        commit_sha: str,
        path: str,
        line: int | None = None,
        side: str = "RIGHT",
        start_line: int | None = None,
    ) -> None:
        """Create a review comment on a pull request.

        Args:
            pr_number: The number of the pull request
            body: The body of the comment
            commit_sha: The SHA of the commit to comment on
            path: The path of the file to comment on
            line: The line number to comment on
            side: The side of the comment to create
            start_line: The start line number to comment on

        Returns:
            None
        """
        return self._op.create_pr_review_comment(pr_number, body, commit_sha, path, line, side, start_line)


# The last 2 lines of code are added to the runner. See codegen-backend/cli/generate/utils.py
# Type Aliases
CodebaseType = Codebase[
    SourceFile,
    Directory,
    Symbol,
    Class,
    Function,
    Import,
    Assignment,
    Interface,
    TypeAlias,
    Parameter,
    CodeBlock,
]
PyCodebaseType = Codebase[
    PyFile,
    PyDirectory,
    PySymbol,
    PyClass,
    PyFunction,
    PyImport,
    PyAssignment,
    Interface,
    TypeAlias,
    PyParameter,
    PyCodeBlock,
]
TSCodebaseType = Codebase[
    TSFile,
    TSDirectory,
    TSSymbol,
    TSClass,
    TSFunction,
    TSImport,
    TSAssignment,
    TSInterface,
    TSTypeAlias,
    TSParameter,
    TSCodeBlock,
]
