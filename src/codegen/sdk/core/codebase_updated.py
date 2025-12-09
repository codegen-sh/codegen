"""Codebase - main interface for Codemods to interact with the codebase"""

from pathlib import Path
from typing import Generic, Literal, overload

from rich.console import Console
from typing_extensions import TypeVar

from codegen.configs.models.codebase import CodebaseConfig, PinkMode
from codegen.configs.models.secrets import SecretsConfig
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.codebase.codebase_context import (
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
from codegen.sdk.core.file import SourceFile
from codegen.sdk.core.function import Function
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.interface import Interface
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.type_alias import TypeAlias
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
from codegen.shared.decorators.docs import apidoc
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
