import os
import sys
from pathlib import Path

import modal
from loguru import logger

from codegen_on_oss.bucket_store import BucketStore
from codegen_on_oss.cache import cachedir
from codegen_on_oss.metrics import MetricsProfiler
from codegen_on_oss.parser import CodegenParser
from codegen_on_oss.sources import RepoSource

parse_app = modal.App("codegen-oss-parse")


@parse_app.function(
    cpu=4,
    memory=16384,
    secrets=[modal.Secret.from_name("codegen-oss-bucket-credentials")],
    volumes={
        str(cachedir.absolute()): modal.Volume.from_name("codegen-oss-repo-volume")
    },
    image=modal.Image.debian_slim(python_version="3.12")
    .pip_install("uv")
    .apt_install("git")  # required by codegen sdk
    .workdir("/app")
    .add_local_file("uv.lock", remote_path="/app/uv.lock", copy=True)
    .add_local_file("pyproject.toml", remote_path="/app/pyproject.toml", copy=True)
    .run_commands("uv sync --frozen --no-install-project")
    .env({"PATH": "/app/.venv/bin:$PATH"})
    .add_local_python_source("codegen_on_oss")
    .add_local_dir("codegen_on_oss", remote_path="/app/codegen_on_oss")
    .add_local_file("input.csv", remote_path="/app/input.csv"),
)
def parse_repo_on_modal(
    source: str,
    env: dict[str, str],
    log_output_path: str = "output.logs",
    metrics_output_path: str = "metrics.csv",
):
    """
    Parse repositories on Modal.

    Args:
        source: The source of the repositories to parse.
        env: The environment variables to use.
        log_output_path: The path to the log file.
        metrics_output_path: The path to the metrics file.
    """
    os.environ.update(env)

    logger.add(
        log_output_path,
        format="{time: HH:mm:ss} {level} {message}",
        level="INFO",
    )
    logger.add(sys.stdout, format="{time: HH:mm:ss} {level} {message}", level="DEBUG")
    repo_source = RepoSource.from_source_type(source)
    metrics_profiler = MetricsProfiler(metrics_output_path)

    parser = CodegenParser(Path(cachedir) / "repositories", metrics_profiler)
    for repo_url, commit_hash in repo_source:
        try:
            parser.parse(repo_url, commit_hash)
        except Exception as e:
            logger.exception(f"Error parsing repository {repo_url}: {e}")

    BucketStore(bucket_name=os.getenv("BUCKET_NAME", "codegen-oss-parse")).upload_run(
        repo_source,
        log_output_path,
        metrics_output_path,
    )


@parse_app.local_entrypoint()
def main():
    """
    Main entrypoint for the parse app.
    """
    parse_repo_on_modal.remote(
        source="csv",
        env={
            "CSV_FILE_PATH": "/app/input.csv",
        },
    )
