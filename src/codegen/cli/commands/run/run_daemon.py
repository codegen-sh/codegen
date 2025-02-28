import rich
import rich_click as click
from rich.panel import Panel

from codegen.cli.auth.session import CodegenSession
from codegen.cli.commands.start.docker_container import DockerContainer
from codegen.cli.errors import ServerError
from codegen.cli.rich.codeblocks import format_command
from codegen.cli.rich.spinners import create_spinner
from codegen.runner.clients.docker_client import DockerClient
from codegen.runner.enums.warmup_state import WarmupState


def run_daemon(session: CodegenSession, function, diff_preview: int | None = None):
    """Run a function on the cloud service.

    Args:
        session: The current codegen session
        function: The function to run
        diff_preview: Number of lines of diff to preview (None for all)
    """
    with create_spinner(f"Running {function.name}...") as status:
        try:
            client = _get_docker_client(session)
            run_output = client.run_function(function, commit=not diff_preview)
            rich.print(f"✅ Ran {function.name} successfully")

            if run_output.logs:
                rich.print("")
                panel = Panel(run_output.logs, title="[bold]Logs[/bold]", border_style="blue", padding=(1, 2), expand=False)
                rich.print(panel)

            if run_output.error:
                rich.print("")
                panel = Panel(run_output.error, title="[bold]Error[/bold]", border_style="red", padding=(1, 2), expand=False)
                rich.print(panel)

            if run_output.observation:
                # Only show diff preview if requested
                if diff_preview:
                    rich.print("")  # Add some spacing

                    # Split and limit diff to requested number of lines
                    diff_lines = run_output.observation.splitlines()
                    truncated = len(diff_lines) > diff_preview
                    limited_diff = "\n".join(diff_lines[:diff_preview])

                    if truncated:
                        limited_diff += f"\n\n...\n\n[yellow]diff truncated to {diff_preview} lines[/yellow]"

                    panel = Panel(limited_diff, title="[bold]Diff Preview[/bold]", border_style="blue", padding=(1, 2), expand=False)
                    rich.print(panel)
            else:
                rich.print("")
                rich.print("[yellow] No changes were produced by this codemod[/yellow]")

            if diff_preview:
                rich.print("[green]✓ Changes have been applied to your local filesystem[/green]")
                rich.print("[yellow]→ Don't forget to commit your changes:[/yellow]")
                rich.print(format_command("git add ."))
                rich.print(format_command("git commit -m 'Applied codemod changes'"))

        except ServerError as e:
            status.stop()
            raise click.ClickException(str(e))


def _get_docker_client(session: CodegenSession) -> DockerClient:
    repo_name = session.config.repository.name
    if (container := DockerContainer.get(repo_name)) is None:
        msg = f"Codegen runner does not exist for {repo_name}. Please run 'codegen start' from {session.config.repository.path}."
        raise click.ClickException(msg)

    if not container.is_running():
        msg = f"Codegen runner for {repo_name} is not running. Please run 'codegen start' from {session.config.repository.path}."
        raise click.ClickException(msg)

    client = DockerClient(container)
    if not client.is_running():
        msg = "Codebase server is not running. Please stop the container and restart."
        raise click.ClickException(msg)

    if client.server_info().warmup_state != WarmupState.COMPLETED:
        msg = "Runner has not finished parsing the codebase. Please wait a moment and try again."
        raise click.ClickException(msg)

    return client
