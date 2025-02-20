from abc import ABC
from pathlib import Path

from dotenv import load_dotenv, set_key
from pydantic import PrivateAttr
from pydantic_settings import BaseSettings, SettingsConfigDict

from codegen.shared.configs.constants import ENV_FILENAME, GLOBAL_ENV_FILE
from codegen.shared.configs.session_manager import session_codegen_dir

_loaded_env_files = set()


class BaseConfig(BaseSettings, ABC):
    """Base class for all config classes.
    Handles loading and saving of configuration values from environment files.
    Supports both global and local config files.
    """

    model_config = SettingsConfigDict(
        extra="ignore",  # Allow extra fields
        env_prefix="",  # This will be set dynamically in __init__
        env_file=None,  # This will be set dynamically in __init__
        case_sensitive=False,
    )
    _prefix: str = PrivateAttr()

    def __init__(self, prefix: str, env_filepath: Path | None = None, *args, **kwargs) -> None:
        if env_filepath is None:
            codegen_dir = session_codegen_dir
            if codegen_dir is not None:
                env_filepath = codegen_dir / ENV_FILENAME

        # Only include env files that exist
        env_filepaths = []
        if GLOBAL_ENV_FILE.exists():
            env_filepaths.append(GLOBAL_ENV_FILE)
        if env_filepath and env_filepath.exists() and env_filepath != GLOBAL_ENV_FILE:
            env_filepaths.append(env_filepath)

        print(f"Loading environment variables for {self.__class__.__name__} using {env_filepaths}")

        self.model_config["env_prefix"] = f"{prefix}_"
        self.model_config["env_file"] = env_filepaths

        super().__init__(*args, **kwargs)
        self._prefix = prefix

    def load_env(self, env_filepath: Path | None, is_global: bool):
        """Load environment variables from .env file based on the environment variable"""
        # if env_filepath in _loaded_env_files:
        #     return

        _loaded_env_files.add(env_filepath)
        # First load from global env file
        if GLOBAL_ENV_FILE.exists():
            print(f"Loading global environment variables from {GLOBAL_ENV_FILE} for {self.__class__.__name__}")
            load_dotenv(dotenv_path=GLOBAL_ENV_FILE)
        else:
            self.write_to_file(GLOBAL_ENV_FILE)

        # Then load from specified codegen dir env file
        if not is_global and env_filepath and env_filepath != GLOBAL_ENV_FILE:
            if env_filepath.exists():
                print(f"Loading local environment variables from {env_filepath} for {self.__class__.__name__}")
                load_dotenv(dotenv_path=env_filepath)
            else:
                self.write_to_file(env_filepath)

    def write_to_file(self, env_filepath: Path):
        """Dump environment variables to a file"""
        env_filepath.parent.mkdir(parents=True, exist_ok=True)

        if not env_filepath.exists():
            with open(env_filepath, "w") as f:
                f.write("")

        # Update with new values
        for key, value in self.model_dump().items():
            set_key(env_filepath, key, str(value))
