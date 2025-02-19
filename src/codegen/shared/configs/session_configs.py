import json
from pathlib import Path

import tomllib

from codegen.shared.configs.constants import CONFIG_PATH, GLOBAL_CONFIG_PATH, SESSION_FILE
from codegen.shared.configs.models.global_config import GlobalConfig
from codegen.shared.configs.models.session import SessionConfig


def load_session_config(config_path: Path, base_config: SessionConfig | None = None) -> SessionConfig:
    """Loads configuration from various sources."""
    base_config = base_config or global_config.global_session
    toml_config = _load_from_toml(config_path)
    config_dict = _merge_configs(base_config.model_dump(), toml_config)
    loaded_config = SessionConfig(**config_dict)
    loaded_config.file_path = str(config_path)

    # Save the configuration to file if it doesn't exist
    if not config_path.exists():
        loaded_config.save()
    return loaded_config


def _load_global_config() -> GlobalConfig:
    """Load configuration from the JSON file."""
    base_session = _load_from_env(GLOBAL_CONFIG_PATH)
    global_session = load_session_config(GLOBAL_CONFIG_PATH, base_config=base_session)

    if SESSION_FILE.exists():
        with open(SESSION_FILE) as f:
            json_config = json.load(f)
            json_config["global_session"] = global_session.model_dump()
            return GlobalConfig.model_validate(json_config, strict=False)

    new_config = GlobalConfig(sessions=[], global_session=global_session)
    new_config.save()
    return new_config


def _load_from_env(config_path: Path) -> SessionConfig:
    """Load configuration from the environment variables."""
    return SessionConfig(file_path=str(config_path))


def _load_from_toml(config_path: Path) -> dict[str, any]:
    """Load configuration from the TOML file."""
    if config_path.exists():
        with open(config_path, "rb") as f:
            toml_config = tomllib.load(f)
            return toml_config
    return {}


def _merge_configs(base: dict, override: dict) -> dict:
    """Recursively merge two dictionaries, with override taking precedence for non-null values."""
    merged = base.copy()
    for key, override_value in override.items():
        if isinstance(override_value, dict) and key in base and isinstance(base[key], dict):
            # Recursively merge nested dictionaries
            merged[key] = _merge_configs(base[key], override_value)
        elif override_value is not None and override_value != "":
            # Override only if value is non-null and non-empty
            merged[key] = override_value
    return merged


global_config = _load_global_config()
config = load_session_config(CONFIG_PATH)


if __name__ == "__main__":
    print(config)
    print(global_config)
