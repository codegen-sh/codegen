import os
from typing import Optional

import rich
import rich_click as click
from rich import box
from rich.panel import Panel

from codegen.cli.utils.memory_profiler import profile_command


@click.command(name="memprof")
@click.argument("command", nargs=-1, required=True)
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(file_okay=False),
    help="Directory to save memory profile reports",
)
def memprof_command(command: list[str], output_dir: Optional[str] = None):
    """Profile memory usage of a Codegen CLI command.

    Example:
        codegen memprof run my-codemod --arguments '{"param": "value"}'
    """
    if not command:
        rich.print("[bold red]Error:[/bold red] No command specified")
        return

    # Convert command tuple to list
    cmd_args = list(command)

    # Set default output directory if not provided
    if not output_dir:
        home_dir = os.path.expanduser("~")
        output_dir = os.path.join(home_dir, ".codegen", "memory_profiles")

    # Run the profiling
    rich.print(
        Panel(
            f"[cyan]Profiling command:[/cyan] codegen {' '.join(cmd_args)}",
            title="🔍 [bold]Memory Profiler[/bold]",
            border_style="cyan",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )

    try:
        report_dir = profile_command(cmd_args, output_dir=output_dir)
        rich.print(
            Panel(
                f"[green]Memory profile saved to:[/green] {report_dir}",
                title="✅ [bold]Profiling Complete[/bold]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
    except Exception as e:
        rich.print(
            Panel(
                f"[red]Error during profiling:[/red] {e!s}",
                title="❌ [bold]Profiling Failed[/bold]",
                border_style="red",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )
