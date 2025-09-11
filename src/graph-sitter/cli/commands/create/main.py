from pathlib import Path

import rich
import rich_click as click

from codegen.sdk.cli.auth.session import CliSession
from codegen.sdk.cli.errors import ServerError
from codegen.sdk.cli.rich.codeblocks import format_command, format_path
from codegen.sdk.cli.rich.pretty_print import pretty_print_error
from codegen.sdk.cli.utils.default_code import DEFAULT_CODEMOD
from codegen.sdk.cli.workspace.decorators import requires_init


def get_target_paths(name: str, path: Path) -> tuple[Path, Path]:
    """Get the target path for the new function file.

    Creates a directory structure like:
    .codegen/codemods/function_name/function_name.py
    """
    # Convert name to snake case for filename
    name_snake = name.lower().replace("-", "_").replace(" ", "_")

    # If path points to a specific file, use its parent directory
    if path.suffix == ".py":
        base_dir = path.parent
    else:
        base_dir = path

    # Create path within .codegen/codemods
    codemods_dir = base_dir / ".codegen" / "codemods"
    function_dir = codemods_dir / name_snake
    codemod_path = function_dir / f"{name_snake}.py"
    prompt_path = function_dir / f"{name_snake}-system-prompt.txt"
    return codemod_path, prompt_path


def make_relative(path: Path) -> str:
    """Convert a path to a relative path from cwd, handling non-existent paths."""
    try:
        return f"./{path.relative_to(Path.cwd())}"
    except ValueError:
        # If all else fails, just return the full path relative to .codegen
        parts = path.parts
        if ".codegen" in parts:
            idx = parts.index(".codegen")
            return "./" + str(Path(*parts[idx:]))
        return f"./{path.name}"


@click.command(name="create")
@requires_init
@click.argument("name", type=str)
@click.argument("path", type=click.Path(path_type=Path), default=None)
@click.option("--overwrite", is_flag=True, help="Overwrites function if it already exists.")
def create_command(session: CliSession, name: str, path: Path | None, overwrite: bool = False):
    """Create a new codegen function.

    NAME is the name/label for the function
    PATH is where to create the function (default: current directory)
    """
    # Get the target path for the function
    codemod_path, prompt_path = get_target_paths(name, path or Path.cwd())

    # Check if file exists
    if codemod_path.exists() and not overwrite:
        rel_path = make_relative(codemod_path)
        pretty_print_error(f"File already exists at {format_path(rel_path)}\n\nTo overwrite the file:\n{format_command(f'gs create {name} {rel_path} --overwrite')}")
        return

    code = None
    try:
        # Use default implementation
        code = DEFAULT_CODEMOD.format(name=name)

        # Create the target directory if needed
        codemod_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the function code
        codemod_path.write_text(code)

    except (ServerError, ValueError) as e:
        raise click.ClickException(str(e))

    # Success message
    rich.print(f"\n✅ {'Overwrote' if overwrite and codemod_path.exists() else 'Created'} function '{name}'")
    rich.print("")
    rich.print("📁 Files Created:")
    rich.print(f"   [dim]Function:[/dim]  {make_relative(codemod_path)}")

    # Next steps
    rich.print("\n[bold]What's next?[/bold]\n")
    rich.print("1. Review and edit the function to customize its behavior")
    rich.print(f"2. Run it with: \n{format_command(f'gs run {name}')}")
