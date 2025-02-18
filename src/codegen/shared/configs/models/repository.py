from pydantic_settings import BaseSettings

from codegen.shared.configs.models.utils import get_setting_config

prefix = "REPOSITORY"


class RepositoryConfig(BaseSettings):
    """Configuration for the repository context to run codegen.
    To populate this config, call `codegen init` from within a git repository.
    """

    model_config = get_setting_config(prefix)

    repo_path: str | None = None  # replace with base_dir
    repo_name: str | None = None
    full_name: str | None = None  # replace with org_name
    language: str | None = None
    user_name: str | None = None
    user_email: str | None = None
