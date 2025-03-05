import importlib.util
import logging
import socket
import subprocess
import sys
from pathlib import Path
from typing import Optional

import rich
import rich_click as click
import uvicorn
from rich.logging import RichHandler
from rich.panel import Panel

from codegen.extensions.events.codegen_app import CodegenApp
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


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
app = app.app  # Get the FastAPI instance from the CodegenApp
"""
    module_path = file_path.parent / f"{module_name}.py"
    module_path.write_text(module_code)

    return f"{module_name}:app"


def start_ngrok(port: int) -> Optional[str]:
    """Start ngrok and return the public URL"""
    try:
        import requests

        # Start ngrok
        process = subprocess.Popen(["ngrok", "http", str(port)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait a moment for ngrok to start
        import time

        time.sleep(2)

        # Get the public URL from ngrok's API
        try:
            response = requests.get("http://localhost:4040/api/tunnels")
            data = response.json()

            # Get the first https URL
            for tunnel in data["tunnels"]:
                if tunnel["proto"] == "https":
                    return tunnel["public_url"]

            logger.warning("No HTTPS tunnel found")
            return None

        except requests.RequestException:
            logger.exception("Failed to get ngrok URL from API")
            logger.info("Get your public URL from: http://localhost:4040")
            return None

    except FileNotFoundError:
        logger.exception("ngrok not found. Please install it first: https://ngrok.com/download")
        return None


def find_available_port(start_port: int = 8000, max_tries: int = 100) -> int:
    """Find an available port starting from start_port."""
    for port in range(start_port, start_port + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", port))
                return port
        except OSError:
            continue
    msg = f"No available ports found between {start_port} and {start_port + max_tries}"
    raise click.ClickException(msg)


@click.command(name="serve")
@click.argument("file", type=click.Path(exists=True, path_type=Path))
@click.option("--host", default="127.0.0.1", help="Host to bind to")
@click.option("--port", default=8000, help="Port to bind to")
@click.option("--debug", is_flag=True, help="Enable debug mode with hot reloading")
@click.option("--public", is_flag=True, help="Expose the server publicly using ngrok")
@click.option("--workers", default=1, help="Number of worker processes")
@click.option("--repos", multiple=True, help="GitHub repositories to analyze")
def serve_command(file: Path, host: str = "127.0.0.1", port: int = 8000, debug: bool = False, public: bool = False, workers: int = 4, repos: list[str] = []):
    """Run a CodegenApp server from a Python file.

    FILE is the path to a Python file containing a CodegenApp instance
    """
    # Configure rich logging
    setup_logging(debug)

    try:
        if debug:
            workers = 1

        # Find available port if the specified one is in use
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((host, port))
        except OSError:
            port = find_available_port(port)
            logger.warning(f"Port {port} was in use, using port {port} instead")

        # Always create module for uvicorn
        app_import_string = create_app_module(file)
        reload_dirs = [str(file.parent)] if debug else None

        # Print server info
        rich.print(
            Panel(
                f"[green]Starting CodegenApp server[/green]\n"
                f"[dim]File:[/dim] {file}\n"
                f"[dim]URL:[/dim] http://{host}:{port}\n"
                f"[dim]Workers:[/dim] {workers}\n"
                f"[dim]Debug:[/dim] {'enabled' if debug else 'disabled'}",
                title="[bold]Server Info[/bold]",
                border_style="blue",
            )
        )

        # Start ngrok if --public flag is set
        if public:
            public_url = start_ngrok(port)
            if public_url:
                logger.info(f"Public URL: {public_url}")
                logger.info("Use these webhook URLs in your integrations:")
                logger.info(f"  Slack: {public_url}/slack/events")
                logger.info(f"  GitHub: {public_url}/github/events")
                logger.info(f"  Linear: {public_url}/linear/events")

        # Run the server with workers
        uvicorn.run(
            app_import_string,
            host=host,
            port=port,
            reload=debug,
            reload_dirs=reload_dirs,
            log_level="debug" if debug else "info",
            workers=workers,
        )

    except Exception as e:
        msg = f"Server error: {e!s}"
        raise click.ClickException(msg)


if __name__ == "__main__":
    serve_command()
