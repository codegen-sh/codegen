from pydantic import Field

from codegen.configs.models.base_config import BaseConfig


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
    generics: bool = True
    import_resolution_overrides: dict[str, str] = Field(default_factory=lambda: {})
    ts_dependency_manager: bool = False
    ts_language_engine: bool = False
    v8_ts_engine: bool = False
    unpacking_assignment_partial_removal: bool = True


DefaultCodebaseConfig = CodebaseConfig()
