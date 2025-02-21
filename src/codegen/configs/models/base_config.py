from abc import ABC
from pathlib import Path

from dotenv import load_dotenv, set_key
from pydantic_settings import BaseSettings, SettingsConfigDict

from codegen.configs.constants import ENV_FILENAME, GLOBAL_ENV_FILE
from codegen.shared.path import get_git_root_path


class BaseConfig(BaseSettings, ABC):
    """Base class for all config classes.
    Handles loading and saving of configuration values from environment files.
    Supports both global and local config files.
    """

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    def __init__(self, prefix: str, env_filepath: Path | None = None, *args, **kwargs) -> None:
        if env_filepath is None:
            root_path = get_git_root_path()
            if root_path is not None:
                env_filepath = root_path / ENV_FILENAME

        # Only include env files that exist
        if GLOBAL_ENV_FILE.exists():
            load_dotenv(GLOBAL_ENV_FILE, override=True)

        if env_filepath and env_filepath.exists() and env_filepath != GLOBAL_ENV_FILE:
            load_dotenv(env_filepath, override=True)

        self.model_config["env_prefix"] = f"{prefix.upper()}_" if len(prefix) > 0 else ""
        super().__init__(*args, **kwargs)

    @property
    def env_prefix(self) -> str:
        return self.model_config["env_prefix"]

    def set(self, env_filepath: Path, key: str, value: str) -> None:
        """Update configuration values"""
        if key.lower() in self.model_fields:
            setattr(self, key.lower(), value)
            set_key(env_filepath, f"{self.model_config['env_prefix']}{key.upper()}", str(value))

    def write_to_file(self, env_filepath: Path) -> None:
        """Dump environment variables to a file"""
        env_filepath.parent.mkdir(parents=True, exist_ok=True)

        if not env_filepath.exists():
            with open(env_filepath, "w") as f:
                f.write("")

        # Update with new values
        for key, value in self.model_dump().items():
            if value is None:
                continue
            set_key(env_filepath, f"{self.model_config['env_prefix']}{key.upper()}", str(value))
