from pydantic_settings import SettingsConfigDict


def get_setting_config(prefix: str) -> SettingsConfigDict:
    return SettingsConfigDict(
        env_prefix=f"{prefix}_",
        case_sensitive=False,
        extra="ignore",
    )
