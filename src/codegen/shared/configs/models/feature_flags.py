from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from codegen.shared.configs.models.utils import get_setting_config

prefix = "FEATURE_FLAGS"


class TypescriptConfig(BaseSettings):
    model_config = get_setting_config(f"{prefix}_TYPESCRIPT")

    ts_dependency_manager: bool = False
    ts_language_engine: bool = False
    v8_ts_engine: bool = False


class CodebaseFeatureFlags(BaseSettings):
    model_config = get_setting_config(f"{prefix}")

    debug: bool = False
    verify_graph: bool = False
    track_graph: bool = False
    method_usages: bool = True
    sync_enabled: bool = True
    full_range_index: bool = False
    ignore_process_errors: bool = True
    disable_graph: bool = False
    generics: bool = True
    import_resolution_overrides: dict[str, str] = Field(default_factory=lambda: {})
    typescript: TypescriptConfig = Field(default_factory=TypescriptConfig)


class FeatureFlagsConfig(BaseModel):
    codebase: CodebaseFeatureFlags = Field(default_factory=CodebaseFeatureFlags)
