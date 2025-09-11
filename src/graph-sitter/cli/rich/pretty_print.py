import rich
from rich import box
from rich.markdown import Markdown
from rich.panel import Panel


def pretty_print_logs(logs: str):
    """Pretty print logs in a panel."""
    rich.print(
        Panel(
            logs,
            title="[bold blue]Logs",
            border_style="blue",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    rich.print()  # spacing


def pretty_print_error(error: str):
    """Pretty print error in a panel."""
    rich.print(
        Panel(
            error,
            title="[bold red]Error",
            border_style="red",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    rich.print()  # spacing


def pretty_print_diff(diff: str):
    """Pretty print diff in a panel."""
    rich.print(
        Panel(
            Markdown(
                f"""```diff\n{diff}\n```""",
                code_theme="monokai",
            ),
            title="[bold green]Diff",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    rich.print()  # spacing
