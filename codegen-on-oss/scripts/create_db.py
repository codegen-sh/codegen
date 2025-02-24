from pydantic_settings import SettingsConfigDict

from codegen_on_oss.outputs.sql_output import Base, SQLSettings, get_session_maker


class DotEnvSQLSettings(SQLSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POSTGRESQL_",
        extra="ignore",
    )


settings = DotEnvSQLSettings()
session_maker = get_session_maker(settings)

with session_maker() as session:
    Base.metadata.create_all(bind=session.bind)
