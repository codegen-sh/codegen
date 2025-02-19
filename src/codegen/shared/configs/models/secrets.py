import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

from codegen.shared.configs.models.utils import get_setting_config

prefix = "SECRETS"


class SecretsConfig(BaseSettings):
    """Configuration for various API secrets and tokens.

    Loads from environment variables with the SECRETS_ prefix.
    Falls back to .env file for missing values.
    """

    model_config = get_setting_config(prefix)

    github_token: str | None = None
    openai_api_key: str | None = None

    def __init__(self, **kwargs):
        """Initialize secrets, loading from .env if needed."""
        super().__init__(**kwargs)

        # Load .env file if it exists
        env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)

        # Try to load from environment if not set
        if not self.github_token:
            self.github_token = os.getenv("GITHUB_TOKEN")

        if not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
