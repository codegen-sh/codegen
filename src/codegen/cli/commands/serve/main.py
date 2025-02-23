import importlib.util
import logging
import sys
from pathlib import Path

import rich
import rich_click as click
import uvicorn
from rich.logging import RichHandler
from rich.panel import Panel

from codegen.extensions.events.codegen_app import CodegenApp


def setup_logging(debug: bool):
    """Configure rich logging with colors."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(message)s",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                tracebacks_show_locals=debug,
                markup=True,
                show_time=False,
            )
        ],
    )


def load_app_from_file(file_path: Path) -> CodegenApp:
    """Load a CodegenApp instance from a Python file.

    Args:
        file_path: Path to the Python file containing the CodegenApp

    Returns:
        The CodegenApp instance from the file

    Raises:
        click.ClickException: If no CodegenApp instance is found
    """
    try:
        # Import the module from file path
        spec = importlib.util.spec_from_file_location("app_module", file_path)
        if not spec or not spec.loader:
            msg = f"Could not load module from {file_path}"
            raise click.ClickException(msg)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find CodegenApp instance
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, CodegenApp):
                return attr

        msg = f"No CodegenApp instance found in {file_path}"
        raise click.ClickException(msg)

    except Exception as e:
        msg = f"Error loading app from {file_path}: {e!s}"
        raise click.ClickException(msg)


def create_app_module(file_path: Path) -> str:
    """Create a temporary module that exports the app for uvicorn."""
    # Add the file's directory to Python path
    file_dir = str(file_path.parent.absolute())
    if file_dir not in sys.path:
        sys.path.insert(0, file_dir)

    # Create a module that imports and exposes the app
    module_name = f"codegen_app_{file_path.stem}"
    module_code = f"""
from {file_path.stem} import app
app = app.app
"""
    module_path = file_path.parent / f"{module_name}.py"
    module_path.write_text(module_code)

    return f"{module_name}:app"


@click.command(name="serve")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--debug", is_flag=True, help="Enable debug mode with hot reloading")
def serve_command(file: Path, host: str = "127.0.0.1", port: int = 8000, debug: bool = False):
    """Run a CodegenApp server from a Python file.

    FILE is the path to a Python file containing a CodegenApp instance
    """
    # Configure rich logging
    setup_logging(debug)

    try:
        if debug:
            # For debug mode, create a module that uvicorn can reload
            app_import_string = create_app_module(file)
            reload_dirs = [str(file.parent)]
        else:
            # For normal mode, load the app directly
            app = load_app_from_file(file)
            app_import_string = app.app

        # Print server info
        rich.print(
            Panel(
                f"[green]Starting CodegenApp server[/green]\n[dim]File:[/dim] {file}\n[dim]URL:[/dim] http://{host}:{port}\n[dim]Debug:[/dim] {'enabled' if debug else 'disabled'}",
                title="[bold]Server Info[/bold]",
                border_style="blue",
            )
        )

        # Run the server
        uvicorn.run(
            app_import_string,
            host=host,
            port=port,
            reload=debug,
            reload_dirs=reload_dirs if debug else None,
            log_level="debug" if debug else "info",
        )

    except Exception as e:
        msg = f"Server error: {e!s}"
        raise click.ClickException(msg)
