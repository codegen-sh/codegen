import json
from pathlib import Path

import toml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from codegen.shared.configs.models.feature_flags import FeatureFlagsConfig
from codegen.shared.configs.models.repository import RepositoryConfig
from codegen.shared.configs.models.secrets import SecretsConfig


class SessionConfig(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        exclude_defaults=False,
    )
    file_path: str
    secrets: SecretsConfig = Field(default_factory=SecretsConfig)
    repository: RepositoryConfig = Field(default_factory=RepositoryConfig)
    feature_flags: FeatureFlagsConfig = Field(default_factory=FeatureFlagsConfig)

    def save(self) -> None:
        """Save configuration to the config file."""
        config_dir = Path(self.file_path).parent
        config_dir.mkdir(parents=True, exist_ok=True)

        with open(self.file_path, "w") as f:
            toml.dump(self.model_dump(exclude_none=True), f)

    def get(self, full_key: str) -> str | None:
        """Get a configuration value as a JSON string."""
        data = self.model_dump()
        keys = full_key.split(".")
        current = data
        for k in keys:
            if not isinstance(current, dict) or k not in current:
                return None
            current = current[k]
        return json.dumps(current)

    def set(self, full_key: str, value: str) -> None:
        """Update a configuration value and save it to the config file.

        Args:
            full_key: Dot-separated path to the config value (e.g. "feature_flags.codebase.debug")
            value: string representing the new value
        """
        data = self.model_dump()
        keys = full_key.split(".")
        current = data
        current_attr = self

        # Traverse through the key path and validate
        for k in keys[:-1]:
            if not isinstance(current, dict) or k not in current:
                msg = f"Invalid configuration path: {full_key}"
                raise KeyError(msg)
            current = current[k]
            current_attr = current_attr.__getattribute__(k)

        if not isinstance(current, dict) or keys[-1] not in current:
            msg = f"Invalid configuration path: {full_key}"
            raise KeyError(msg)

        # Validate the value type at key
        field_info = current_attr.model_fields[keys[-1]].annotation
        if isinstance(field_info, BaseModel):
            try:
                SessionConfig.model_validate(value, strict=False)
            except Exception as e:
                msg = f"Value does not match the expected type for key: {full_key}\n\nError:{e}"
                raise ValueError(msg)

        # Set the key value
        if isinstance(current[keys[-1]], dict):
            try:
                current[keys[-1]] = json.loads(value)
            except json.JSONDecodeError as e:
                msg = f"Value must be a valid JSON object for key: {full_key}\n\nError:{e}"
                raise ValueError(msg)
        else:
            current[keys[-1]] = value

        # Update the Config object with the new data
        self.__dict__.update(self.__class__.model_validate(data).__dict__)

        # Save to config file
        self.save()

    def __str__(self) -> str:
        """Return a pretty-printed string representation of the config."""
        return json.dumps(self.model_dump(exclude_none=False), indent=2)
