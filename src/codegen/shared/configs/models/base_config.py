from abc import ABC
from pathlib import Path

from dotenv import set_key
from pydantic_settings import BaseSettings, SettingsConfigDict

from codegen.shared.configs.constants import ENV_FILENAME, GLOBAL_ENV_FILE
from codegen.shared.configs.session_manager import session_root


class BaseConfig(BaseSettings, ABC):
    """Base class for all config classes.
    Handles loading and saving of configuration values from environment files.
    Supports both global and local config files.
    """

    model_config = SettingsConfigDict(extra="ignore", case_sensitive=False)

    def __init__(self, prefix: str, env_filepath: Path | None = None, *args, **kwargs) -> None:
        if env_filepath is None:
            root_path = session_root
            if root_path is not None:
                env_filepath = root_path / ENV_FILENAME

        # Only include env files that exist
        env_filepaths = []
        if GLOBAL_ENV_FILE.exists():
            env_filepaths.append(GLOBAL_ENV_FILE)
        if env_filepath and env_filepath.exists() and env_filepath != GLOBAL_ENV_FILE:
            env_filepaths.append(env_filepath)

        self.model_config["env_prefix"] = f"{prefix.upper()}_" if len(prefix) > 0 else ""
        self.model_config["env_file"] = env_filepaths

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
