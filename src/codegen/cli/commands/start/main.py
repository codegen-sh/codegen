import platform as py_platform
import subprocess
from importlib.metadata import version
from pathlib import Path

import click
import rich
from rich.box import ROUNDED
from rich.panel import Panel

from codegen.cli.commands.start.docker_container import DockerContainer
from codegen.cli.commands.start.docker_fleet import CODEGEN_RUNNER_IMAGE
from codegen.configs.models.secrets import SecretsConfig
from codegen.git.repo_operator.local_git_repo import LocalGitRepo
from codegen.git.schemas.repo_config import RepoConfig
from codegen.shared.network.port import get_free_port

_default_host = "0.0.0.0"


@click.command(name="start")
@click.option("--port", "-p", type=int, default=None, help="Port to run the server on")
@click.option("--detached", "-d", is_flag=True, help="Run the server in detached mode")
@click.option("--skip-build", is_flag=True, help="Skip building the Docker image")
@click.option("--force", "-f", is_flag=True, help="Force start the server even if it is already running")
def start_command(port: int | None, detached: bool = False, skip_build: bool = False, force: bool = False) -> None:
    """Starts a local codegen server"""
    repo_path = Path.cwd().resolve()
    repo_config = RepoConfig.from_repo_path(str(repo_path))
    if (container := DockerContainer.get(repo_config.name)) is not None:
        if force:
            rich.print(f"[yellow]Removing existing runner {repo_config.name} to force restart[/yellow]")
            container.remove()
        else:
            return _handle_existing_container(repo_config, container)

    if port is None:
        port = get_free_port()

    try:
        if not skip_build:
            codegen_root = Path(__file__).parent.parent.parent.parent.parent.parent
            codegen_version = version("codegen")
            _build_docker_image(codegen_root=codegen_root, codegen_version=codegen_version)
        _run_docker_container(repo_config, port, detached)
        rich.print(Panel(f"[green]Server started successfully![/green]\nAccess the server at: [bold]http://{_default_host}:{port}[/bold]", box=ROUNDED, title="Codegen Server"))
        # TODO: memory snapshot here
    except Exception as e:
        rich.print(f"[bold red]Error:[/bold red] {e!s}")
        raise click.Abort()


def _handle_existing_container(repo_config: RepoConfig, container: DockerContainer) -> None:
    if container.is_running():
        rich.print(
            Panel(
                f"[green]Codegen server for {repo_config.name} is already running at: [bold]http://{container.host}:{container.port}[/bold][/green]",
                box=ROUNDED,
                title="Codegen Server",
            )
        )
        return

    if container.start():
        rich.print(Panel(f"[yellow]Docker container for {repo_config.name} is not running. Restarting...[/yellow]", box=ROUNDED, title="Docker Session"))
        return

    rich.print(Panel(f"[red]Failed to restart container for {repo_config.name}[/red]", box=ROUNDED, title="Docker Session"))
    click.Abort()


def _build_docker_image(codegen_root: Path, codegen_version: str) -> None:
    build_type = _get_build_type(codegen_version)
    build_cmd = [
        "docker",
        "buildx",
        "build",
        "--platform",
        _get_platform(),
        "-f",
        str(Path(__file__).parent / "Dockerfile"),
        "-t",
        "codegen-runner",
        "--build-arg",
        f"CODEGEN_VERSION={codegen_version}",
        "--build-arg",
        f"BUILD_TYPE={build_type}",
        "--load",
    ]

    # Only add the context path if we're doing a local build
    if build_type == "dev":
        build_cmd.append(str(codegen_root))
    else:
        build_cmd.append(".")  # Minimal context when installing from PyPI

    rich.print(
        Panel(
            f"{str.join(' ', build_cmd)}",
            box=ROUNDED,
            title=f"Running Build Command ({build_type})",
            style="blue",
            padding=(1, 1),
        )
    )
    subprocess.run(build_cmd, check=True)


def _get_build_type(version: str) -> str:
    """Get the build type based on the version string."""
    return "dev" if "dev" in version or "+" in version else "release"


def _get_platform() -> str:
    machine = py_platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        return "linux/amd64"
    elif machine in ("arm64", "aarch64"):
        return "linux/arm64"
    else:
        rich.print(f"[yellow]Warning: Unknown architecture {machine}, defaulting to linux/amd64[/yellow]")
        return "linux/amd64"


def _run_docker_container(repo_config: RepoConfig, port: int, detached: bool) -> None:
    rich.print("[bold blue]Starting Docker container...[/bold blue]")
    container_repo_path = f"/app/git/{repo_config.name}"
    name_args = ["--name", f"{repo_config.name}"]
    envvars = {
        "REPOSITORY_LANGUAGE": repo_config.language.value,
        "REPOSITORY_OWNER": LocalGitRepo(repo_config.repo_path).owner,
        "REPOSITORY_PATH": container_repo_path,
        "GITHUB_TOKEN": SecretsConfig().github_token,
        "PYTHONUNBUFFERED": "1",  # Ensure Python output is unbuffered
        "CODEBASE_SYNC_ENABLED": "True",
    }
    envvars_args = [arg for k, v in envvars.items() for arg in ("--env", f"{k}={v}")]
    mount_args = ["-v", f"{repo_config.repo_path}:{container_repo_path}"]
    entry_point = f"uv run --frozen uvicorn codegen.runner.servers.local_daemon:app --host {_default_host} --port {port}"
    port_args = ["-p", f"{port}:{port}"]
    detached_args = ["-d"] if detached else []
    run_cmd = ["docker", "run", "--rm", *detached_args, *port_args, *name_args, *mount_args, *envvars_args, CODEGEN_RUNNER_IMAGE, entry_point]

    rich.print(
        Panel(
            f"{str.join(' ', run_cmd)}",
            box=ROUNDED,
            title="Running Run Command",
            style="blue",
            padding=(1, 1),
        )
    )
    subprocess.run(run_cmd, check=True)

    if detached:
        rich.print("[yellow]Container started in detached mode. To view logs, run:[/yellow]")
        rich.print(f"[bold]docker logs -f {repo_config.name}[/bold]")
