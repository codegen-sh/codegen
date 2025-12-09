"""Codebase - main interface for Codemods to interact with the codebase"""

from pathlib import Path
from typing import Generic, Literal, overload

import rich.repr
from rich.console import Console
from typing_extensions import TypeVar, deprecated

from codegen.configs.models.codebase import CodebaseConfig, PinkMode
from codegen.configs.models.secrets import SecretsConfig
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk._proxy import proxy_property
from codegen.sdk.codebase.codebase_context import (
    GLOBAL_FILE_IGNORE_LIST,
    CodebaseContext,
)
from codegen.sdk.codebase.config import ProjectConfig
from codegen.sdk.codebase.io.io import IO
from codegen.sdk.codebase.progress.progress import Progress
from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.detached_symbols.code_block import CodeBlock
from codegen.sdk.core.detached_symbols.parameter import Parameter
from codegen.sdk.core.directory import Directory
from codegen.sdk.core.export import Export
from codegen.sdk.core.file import File, SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.interface import Interface
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.type_alias import TypeAlias
from codegen.sdk.enums import NodeType, SymbolType
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.output.constants import ANGULAR_STYLE
from codegen.sdk.python.class_definition import PyClass
from codegen.sdk.python.file import PyFile
from codegen.sdk.python.function import PyFunction
from codegen.sdk.python.import_resolution import PyImport
from codegen.sdk.python.statements.import_statement import PyImportStatement
from codegen.sdk.python.symbol import PySymbol
from codegen.sdk.typescript.class_definition import TSClass
from codegen.sdk.typescript.file import TSFile
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.import_resolution import TSImport
from codegen.sdk.typescript.statements.import_statement import TSImportStatement
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.shared.decorators.docs import apidoc, noapidoc
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger
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
        lazy_parse: bool = False,
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
        lazy_parse: bool = False,
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
        lazy_parse: bool = False,
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

        # Create config if not provided
        if config is None:
            config = CodebaseConfig()

        # Enable lazy parsing if requested
        if lazy_parse:
            config.exp_lazy_graph = True

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
