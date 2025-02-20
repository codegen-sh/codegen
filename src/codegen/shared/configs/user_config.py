import json
from pathlib import Path

from dotenv import set_key
from pydantic import Field

from codegen.shared.configs.constants import GLOBAL_ENV_FILE
from codegen.shared.configs.models.codebase import CodebaseConfig
from codegen.shared.configs.models.repository import RepositoryConfig
from codegen.shared.configs.models.secrets import SecretsConfig


class UserConfig:
    env_filepath: Path
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)
    codebase: CodebaseConfig = Field(default_factory=CodebaseConfig)
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)

    def __init__(self, env_filepath: Path) -> None:
        self.env_filepath = env_filepath
        self.secrets = SecretsConfig(env_filepath=env_filepath)
        self.repository = RepositoryConfig(env_filepath=env_filepath)
        self.codebase = CodebaseConfig(env_filepath=env_filepath)

    def save(self) -> None:
        """Save configuration to the config file."""
        self.env_filepath.parent.mkdir(parents=True, exist_ok=True)
        self.repository.write_to_file(self.env_filepath)
        self.secrets.write_to_file(self.env_filepath)
        self.codebase.write_to_file(self.env_filepath)

    def to_dict(self) -> dict:
        """Return a dictionary representation of the config."""
        config_dict = {}
        # Add repository configs with 'repository_' prefix
        for key, value in self.repository.model_dump().items():
            config_dict[f"{self.repository.env_prefix}{key}".upper()] = value

        # Add secrets configs with 'secrets_' prefix
        for key, value in self.secrets.model_dump().items():
            config_dict[f"{self.secrets.env_prefix}{key}".upper()] = value

        # Add feature flags configs with 'feature_flags_' prefix
        for key, value in self.codebase.model_dump().items():
            config_dict[f"{self.codebase.env_prefix}{key}".upper()] = value
        return config_dict

    def get(self, full_key: str) -> str | None:
        """Get a configuration value"""
        return self.to_dict().get(full_key, None)

    def set(self, full_key: str, value: str) -> None:
        """Update a configuration value and save it to the .env file."""
        # Update with new values
        set_key(self.env_filepath, full_key, str(value))

    def __str__(self) -> str:
        """Return a pretty-printed string representation of the config."""
        return json.dumps(self.to_dict(), indent=2)


global_config = UserConfig(env_filepath=GLOBAL_ENV_FILE)
