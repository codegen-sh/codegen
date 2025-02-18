from pydantic_settings import SettingsConfigDict


def get_setting_config(group_name: str) -> SettingsConfigDict:
    return SettingsConfigDict(
        env_prefix=f"CODEGEN_{group_name}__",
        case_sensitive=False,
        extra="ignore",
        exclude_defaults=False,
    )
