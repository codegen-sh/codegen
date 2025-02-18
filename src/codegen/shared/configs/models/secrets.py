from pydantic_settings import BaseSettings

from codegen.shared.configs.models.utils import get_setting_config

prefix = "SECRETS"


class SecretsConfig(BaseSettings):
    model_config = get_setting_config(prefix)

    github_token: str | None = None
    openai_api_key: str | None = None
