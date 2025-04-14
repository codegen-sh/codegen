from typing import Any

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

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

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    repo: Mapped[str] = mapped_column(String, index=True)
    revision: Mapped[str] = mapped_column(String, index=True)
    language: Mapped[str] = mapped_column(String, index=True)
    action: Mapped[str] = mapped_column(String, index=True)
    codegen_version: Mapped[str] = mapped_column(String, index=True)
    delta_time: Mapped[float] = mapped_column(Float, index=True)
    cumulative_time: Mapped[float] = mapped_column(Float, index=True)
    cpu_time: Mapped[float] = mapped_column(Float, index=True)
    memory_usage: Mapped[int] = mapped_column(Integer, index=True)
    memory_delta: Mapped[int] = mapped_column(Integer, index=True)
    error: Mapped[str] = mapped_column(String, index=True)
    modal_function_call_id: Mapped[str] = mapped_column(String)

    __table_args__ = (
        UniqueConstraint(
            "repo",
            "revision",
            "action",
            "codegen_version",
            name="uq_repo_revision_action_codegen_version",
        ),
    )


class SWEBenchResult(Base):
    __tablename__ = "swebench_output"

    id: Mapped[int] = mapped_column(primary_key=True)
    codegen_version: Mapped[str] = mapped_column(index=True)
    submitted: Mapped[int]
    completed_instances: Mapped[int]
    resolved_instances: Mapped[int]
    unresolved_instances: Mapped[int]
    empty_patches: Mapped[int]
    error_instances: Mapped[int]


class ParseMetricsSQLOutput(BaseOutput):
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


class SWEBenchSQLOutput(BaseOutput):
    def __init__(self, modal_function_call_id: str):
        self.modal_function_call_id = modal_function_call_id
        settings = SQLSettings()
        self.session_maker = get_session_maker(settings)
        super().__init__(
            fields=[
                "instance_id",
                "modal_function_call_id",
                "errored",
                "output",
                "report",
            ]
        )

    def write_output(self, value: dict[str, Any]):
        with self.session_maker() as session:
            stmt = insert(SWEBenchResult).values(
                **value, modal_function_call_id=self.modal_function_call_id
            )
            session.execute(stmt)
            session.commit()
