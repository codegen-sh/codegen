import subprocess
from importlib.metadata import version
from pathlib import Path

import click
import rich
from rich.box import ROUNDED
from rich.panel import Panel

from codegen.cli.auth.session import CodegenSession
from codegen.cli.workspace.decorators import requires_init


@click.command(name="start")
@requires_init
@click.option("--platform", "-t", type=click.Choice(["linux/amd64", "linux/arm64", "linux/amd64,linux/arm64"]), default="linux/amd64,linux/arm64", help="Target platform(s) for the Docker image")
@click.option("--port", "-p", type=int, default=8000)
@click.option("--detached", "-d", is_flag=True, default=False, help="Starts up the server as detached background process")
def start_command(session: CodegenSession, port: int, platform: str, detached: bool):
    """Starts a local codegen server"""
    codegen_version = version("codegen")
    rich.print(codegen_version)
    repo_root = Path(__file__).parent.parent.parent.parent.parent.parent
    dockerfile_path = repo_root / "Dockerfile-runner"

    # Build the Docker image
    rich.print("[bold blue]Building Docker image...[/bold blue]")
    build_cmd = [
        "docker",
        "buildx",
        "build",
        "--platform",
        platform,
        "-f",
        str(dockerfile_path),
        "-t",
        "codegen-runner",
        "--load",
        str(repo_root),
    ]
    rich.print(f"build_cmd: {str.join(' ', build_cmd)}")

    try:
        subprocess.run(build_cmd, check=True)

        # Run the Docker container
        rich.print("[bold blue]Starting Docker container...[/bold blue]")
        run_mode = "-d" if detached else "-it"
        entry_point = f'"uv run --frozen uvicorn codegen.runner.sandbox.server:app --host 0.0.0.0 --port {port}"'
        run_cmd = ["docker", "run", run_mode, "-p", f"8000:{port}", "codegen-runner", entry_point]

        rich.print(f"run_cmd: {str.join(' ', run_cmd)}")
        subprocess.run(run_cmd, check=True)

        rich.print(Panel(f"[green]Server started successfully![/green]\nAccess the server at: [bold]http://0.0.0.0:{port}[/bold]", box=ROUNDED, title="Codegen Server"))

    except subprocess.CalledProcessError as e:
        rich.print(f"[bold red]Error:[/bold red] Failed to {e.cmd[0]} Docker container")
        raise click.Abort()
    except Exception as e:
        rich.print(f"[bold red]Error:[/bold red] {e!s}")
        raise click.Abort()
