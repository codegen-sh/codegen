from pathlib import Path

import rich
import rich_click as click
from rich.table import Table

from codegen.cli.rich.codeblocks import format_codeblock, format_command
from codegen.cli.utils.codemod_manager import CodemodManager


@click.command(name="list")
def list_command():
    """List available codegen functions."""
    functions = CodemodManager.get_decorated()
    if functions:
        table = Table(title="Codegen Functions", border_style="blue")
        table.add_column("Name", style="cyan")
        table.add_column("Type", style="magenta")
        table.add_column("Path", style="dim")
        table.add_column("Subdirectories", style="dim")
        table.add_column("Language", style="dim")

        for func in functions:
            func_type = "Webhook" if func.lint_mode else "Function"
            table.add_row(
                func.name,
                func_type,
                str(func.filepath.relative_to(Path.cwd())) if func.filepath else "<unknown>",
                ", ".join(func.subdirectories) if func.subdirectories else "",
                func.language or "",
            )

        rich.print(table)
        rich.print("\nRun a function with:")
        rich.print(format_command("codegen run <label>"))
    else:
        rich.print("[yellow]No codegen functions found in current directory.[/yellow]")
        rich.print("\nAdd a function with @codegen.function decorator:")
        rich.print(format_codeblock("@codegen.function('label')"))
