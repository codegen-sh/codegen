import logging

import rich
import typer
from rich.table import Table

from codegen.cli.commands.config.telemetry import telemetry_app
from codegen.configs.constants import ENV_FILENAME, GLOBAL_ENV_FILE
from codegen.configs.user_config import UserConfig
from codegen.shared.logging.get_logger import get_logger
from codegen.shared.path import get_git_root_path

# Initialize logger for config commands
logger = get_logger(__name__)

# Create a Typer app for the config command
config_command = typer.Typer(help="Manage codegen configuration.")

# Add telemetry subcommands
config_command.add_typer(telemetry_app, name="telemetry")


@config_command.command(name="list")
def list_config():
    """List current configuration values."""
    logger.info("Config list command invoked", extra={"operation": "config.list", "command": "codegen config list"})

    def flatten_dict(data: dict, prefix: str = "") -> dict:
        items = {}
        for key, value in data.items():
            full_key = f"{prefix}{key}" if prefix else key
            if isinstance(value, dict):
                # Always include dictionary fields, even if empty
                if not value:
                    items[full_key] = "{}"
                items.update(flatten_dict(value, f"{full_key}."))
            else:
                items[full_key] = value
        return items

    config = _get_user_config()
    flat_config = flatten_dict(config.to_dict())
    sorted_items = sorted(flat_config.items(), key=lambda x: x[0])

    # Create table
    table = Table(title="Configuration Values", border_style="blue", show_header=True, title_justify="center")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    # Group items by prefix
    codebase_items = []
    repository_items = []
    other_items = []

    for key, value in sorted_items:
        prefix = key.split("_")[0].lower()
        if prefix == "codebase":
            codebase_items.append((key, value))
        elif prefix == "repository":
            repository_items.append((key, value))
        else:
            other_items.append((key, value))

    # Add codebase section
    if codebase_items:
        table.add_section()
        table.add_row("[bold yellow]Codebase[/bold yellow]", "")
        for key, value in codebase_items:
            table.add_row(f"  {key}", str(value))

    # Add repository section
    if repository_items:
        table.add_section()
        table.add_row("[bold yellow]Repository[/bold yellow]", "")
        for key, value in repository_items:
            table.add_row(f"  {key}", str(value))

    # Add other section
    if other_items:
        table.add_section()
        table.add_row("[bold yellow]Other[/bold yellow]", "")
        for key, value in other_items:
            table.add_row(f"  {key}", str(value))

    rich.print(table)


@config_command.command(name="get")
def get_config(key: str = typer.Argument(..., help="Configuration key to get")):
    """Get a configuration value."""
    logger.info("Config get command invoked", extra={"operation": "config.get", "key": key, "command": f"codegen config get {key}"})

    config = _get_user_config()
    if not config.has_key(key):
        logger.warning("Config key not found", extra={"operation": "config.get", "key": key, "error_type": "key_not_found"})
        rich.print(f"[red]Error: Configuration key '{key}' not found[/red]")
        return

    value = config.get(key)
    # Don't log debug info for successful value retrieval - focus on user actions

    rich.print(f"[cyan]{key}[/cyan]=[magenta]{value}[/magenta]")


@config_command.command(name="set")
def set_config(key: str = typer.Argument(..., help="Configuration key to set"), value: str = typer.Argument(..., help="Configuration value to set")):
    """Set a configuration value and write to .env"""
    config = _get_user_config()
    if not config.has_key(key):
        rich.print(f"[red]Error: Configuration key '{key}' not found[/red]")
        return

    cur_value = config.get(key)
    if cur_value is None or str(cur_value).lower() != value.lower():
        try:
            config.set(key, value)
        except Exception as e:
            logging.exception(e)
            rich.print(f"[red]{e}[/red]")
            return

    rich.print(f"[green]Successfully set {key}=[magenta]{value}[/magenta] and saved to {ENV_FILENAME}[/green]")


def _get_user_config() -> UserConfig:
    if (project_root := get_git_root_path()) is None:
        env_filepath = GLOBAL_ENV_FILE
    else:
        env_filepath = project_root / ENV_FILENAME

    return UserConfig(env_filepath)
