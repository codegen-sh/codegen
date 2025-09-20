import rich
from rich import box
from rich.markdown import Markdown
from rich.panel import Panel

from codegen.cli.api.schemas import RunCodemodOutput


def pretty_print_output(output: RunCodemodOutput):
    """Pretty print the codemod run output with panels."""
    if output.web_link:
        rich.print("\n• [blue underline]" + output.web_link + "[/blue underline]\n")

    if output.logs:
        pretty_print_logs(output.logs)

    if output.error:
        pretty_print_error(output.error)

    if output.observation:
        pretty_print_diff(output.observation)


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
