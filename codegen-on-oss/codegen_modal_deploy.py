import sys
from pathlib import Path

import modal
from loguru import logger

from codegen_on_oss.cache import cachedir
from codegen_on_oss.metrics import MetricsProfiler
from codegen_on_oss.outputs.sql_output import ParseMetricsSQLOutput
from codegen_on_oss.parser import CodegenParser

app = modal.App("codegen-oss-parse")


codegen_repo_volume = modal.Volume.from_name(
    "codegen-oss-repo-volume",
    create_if_missing=True,
)


aws_secrets = modal.Secret.from_name(
    "codegen-oss-parse-secrets",
)


@app.function(
    name="parse_repo",
    concurrency_limit=10,
    cpu=4,
    memory=16384,
    timeout=3600 * 8,
    secrets=[aws_secrets],
    volumes={
        str(cachedir.absolute()): codegen_repo_volume,
    },
    proxy=modal.Proxy.from_name("codegen-parse-proxy"),
    image=modal.Image.debian_slim(python_version="3.13")
    .pip_install("uv")
    .apt_install("git")  # required by codegen sdk
    .env({"PATH": "/app/.venv/bin:$PATH"})
    .workdir("/app")
    .add_local_file("uv.lock", remote_path="/app/uv.lock", copy=True)
    .add_local_file("pyproject.toml", remote_path="/app/pyproject.toml", copy=True)
    .run_commands("uv sync --frozen --no-install-project --extra sql")
    .add_local_python_source("codegen_on_oss", copy=True),
    # .add_local_python_source("codegen_on_oss"),
    # .add_local_dir("codegen_on_oss", remote_path="/app/codegen_on_oss"),
)
def parse_repo(
    repo_url: str,
    commit_hash: str | None,
    language: str | None = None,
):
    """
    Parse repositories on Modal.

    Args:
        repo_url: The URL of the repository to parse.
        commit_hash: The commit hash of the repository to parse.
    """
    logger.add(sys.stdout, format="{time: HH:mm:ss} {level} {message}", level="DEBUG")

    output = ParseMetricsSQLOutput(
        modal_function_call_id=modal.current_function_call_id()
    )
    metrics_profiler = MetricsProfiler(output)
    parser = CodegenParser(Path(cachedir) / "repositories", metrics_profiler)
    # Refresh any updating repo data from other instances
    codegen_repo_volume.reload()
    try:
        parser.parse(repo_url, language, commit_hash)
    except Exception as e:
        logger.exception(f"Error parsing repository {repo_url}: {e}")
    finally:
        # Commit any cache changes to the repo volume
        codegen_repo_volume.commit()
