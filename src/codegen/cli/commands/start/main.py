import subprocess
from importlib.metadata import version
from pathlib import Path

import click
import rich
from rich.box import ROUNDED
from rich.panel import Panel

from codegen.cli.commands.start.docker_container import DockerContainer
from codegen.cli.commands.start.docker_fleet import CODEGEN_RUNNER_IMAGE, DockerFleet
from codegen.configs.models.secrets import SecretsConfig
from codegen.git.repo_operator.local_git_repo import LocalGitRepo
from codegen.git.schemas.repo_config import RepoConfig
from codegen.shared.network.port import get_free_port

_default_host = "0.0.0.0"


@click.command(name="start")
@click.option("--platform", "-t", type=click.Choice(["linux/amd64", "linux/arm64", "linux/amd64,linux/arm64"]), default="linux/amd64,linux/arm64", help="Target platform(s) for the Docker image")
@click.option("--port", "-p", type=int, default=None, help="Port to run the server on")
def start_command(port: int | None, platform: str):
    """Starts a local codegen server"""
    repo_path = Path.cwd().resolve()
    repo_config = RepoConfig.from_repo_path(str(repo_path))
    fleet = DockerFleet.load()
    if (container := fleet.get(repo_config.name)) is not None:
        return _handle_existing_container(repo_config, container)

    codegen_version = version("codegen")
    rich.print(f"[bold green]Codegen version:[/bold green] {codegen_version}")
    codegen_root = Path(__file__).parent.parent.parent.parent.parent.parent
    if port is None:
        port = get_free_port()

    try:
        rich.print("[bold blue]Building Docker image...[/bold blue]")
        _build_docker_image(codegen_root, platform)
        rich.print("[bold blue]Starting Docker container...[/bold blue]")
        _run_docker_container(repo_config, port)
        rich.print(Panel(f"[green]Server started successfully![/green]\nAccess the server at: [bold]http://{_default_host}:{port}[/bold]", box=ROUNDED, title="Codegen Server"))
        # TODO: memory snapshot here
    except subprocess.CalledProcessError as e:
        rich.print(f"[bold red]Error:[/bold red] Failed to {e.cmd[0]} Docker container")
        raise click.Abort()
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


def _build_docker_image(codegen_root: Path, platform: str) -> None:
    build_cmd = [
        "docker",
        "buildx",
        "build",
        "--platform",
        platform,
        "-f",
        str(codegen_root / "Dockerfile-runner"),
        "-t",
        "codegen-runner",
        "--load",
        str(codegen_root),
    ]
    rich.print(f"build_cmd: {str.join(' ', build_cmd)}")
    subprocess.run(build_cmd, check=True)


def _run_docker_container(repo_config: RepoConfig, port: int) -> None:
    container_repo_path = f"/app/git/{repo_config.name}"
    name_args = ["--name", f"{repo_config.name}"]
    envvars = {
        "REPOSITORY_LANGUAGE": repo_config.language.value,
        "REPOSITORY_OWNER": LocalGitRepo(repo_config.repo_path).owner,
        "REPOSITORY_PATH": container_repo_path,
        "GITHUB_TOKEN": SecretsConfig().github_token,
    }
    envvars_args = [arg for k, v in envvars.items() for arg in ("--env", f"{k}={v}")]
    mount_args = ["-v", f"{repo_config.repo_path}:{container_repo_path}"]
    entry_point = f"uv run --frozen uvicorn codegen.runner.sandbox.server:app --host {_default_host} --port {port}"
    run_cmd = ["docker", "run", "-d", "-p", f"{port}:{port}", *name_args, *mount_args, *envvars_args, CODEGEN_RUNNER_IMAGE, entry_point]

    rich.print(f"run_cmd: {str.join(' ', run_cmd)}")
    subprocess.run(run_cmd, check=True)
