from typing import Any

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Column, Float, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .base import BaseOutput


class Base(DeclarativeBase):
    pass


class SQLSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRESQL_")
    host: str = "localhost"
    port: int = 5432
    user: str = "postgres"
    password: str = "postgres"  # noqa: S105
    database: str = "postgres"
    dialect: str = "postgresql"

    @computed_field
    def url(self) -> str:
        return f"{self.dialect}://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


def get_session_maker(settings: SQLSettings):
    engine = create_engine(settings.url)
    return sessionmaker(bind=engine)


class ParseMetrics(Base):
    __tablename__ = "parse_metrics"

    id = Column(Integer, primary_key=True)
    repo = Column(String, index=True)
    revision = Column(String, index=True)
    language = Column(String, index=True)
    action = Column(String, index=True)
    codegen_version = Column(String, index=True)
    delta_time = Column(Float, index=True)
    cumulative_time = Column(Float, index=True)
    cpu_time = Column(Float, index=True)
    memory_usage = Column(Integer, index=True)
    memory_delta = Column(Integer, index=True)
    error = Column(String, index=True)
    modal_function_call_id = Column(String)

    __table_args__ = (
        UniqueConstraint(
            "repo",
            "revision",
            "action",
            "codegen_version",
            name="uq_repo_revision_action_codegen_version",
        ),
    )


class PostgresSQLOutput(BaseOutput):
    extras: dict[str, Any]

    def __init__(self, modal_function_call_id: str):
        super().__init__(
            fields=[
                "repo",
                "revision",
                "action",
                "codegen_version",
                "delta_time",
                "cumulative_time",
                "cpu_time",
                "memory_usage",
                "memory_delta",
                "error",
                "modal_function_call_id",
            ]
        )
        self.modal_function_call_id = modal_function_call_id
        settings = SQLSettings()
        self.session_maker = get_session_maker(settings)

    def write_output(self, value: dict[str, Any]):
        with self.session_maker() as session:
            stmt = insert(ParseMetrics).values(
                **value, modal_function_call_id=self.modal_function_call_id
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[
                    ParseMetrics.repo,
                    ParseMetrics.revision,
                    ParseMetrics.action,
                    ParseMetrics.codegen_version,
                ],
                set_={
                    k: v
                    for k, v in value.items()
                    if k
                    not in (
                        "repo",
                        "revision",
                        "action",
                        "codegen_version",
                        "id",
                    )
                },
            )
            session.execute(stmt)
            session.commit()
