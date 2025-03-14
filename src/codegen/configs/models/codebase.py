from enum import IntEnum, auto

from pydantic import Field

from codegen.configs.models.base_config import BaseConfig


class PinkMode(IntEnum):
    # Use the python SDK for all files
    OFF = auto()
    # Use the Rust SDK for all files
    ALL_FILES = auto()
    # Use the Rust SDK for files the python SDK can't parse (non-source files)
    NON_SOURCE_FILES = auto()


class CodebaseConfig(BaseConfig):
    def __init__(self, prefix: str = "CODEBASE", *args, **kwargs) -> None:
        super().__init__(prefix=prefix, *args, **kwargs)

    debug: bool = False
    verify_graph: bool = False
    track_graph: bool = False
    method_usages: bool = True
    sync_enabled: bool = False
    full_range_index: bool = False
    ignore_process_errors: bool = True
    disable_graph: bool = False
    disable_file_parse: bool = False
    exp_lazy_graph: bool = False
    generics: bool = True
    import_resolution_paths: list[str] = Field(default_factory=lambda: [])
    import_resolution_overrides: dict[str, str] = Field(default_factory=lambda: {})
    py_resolve_syspath: bool = False
    allow_external: bool = False
    ts_dependency_manager: bool = False
    ts_language_engine: bool = False
    v8_ts_engine: bool = False
    unpacking_assignment_partial_removal: bool = True
    use_pink: PinkMode = PinkMode.OFF


DefaultCodebaseConfig = CodebaseConfig()
