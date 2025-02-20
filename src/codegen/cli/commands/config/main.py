import logging
from itertools import groupby

import rich
import rich_click as click
from rich.table import Table

from codegen.shared.configs.constants import CODEGEN_DIR_NAME, ENV_FILENAME, GLOBAL_ENV_FILE
from codegen.shared.configs.session_manager import session_manager
from codegen.shared.configs.user_config import UserConfig


@click.group(name="config")
def config_command():
    """Manage codegen configuration."""
    pass


@config_command.command(name="list")
@click.option("--global", "is_global", is_flag=True, help="Lists the global configuration values")
def list_command(is_global: bool):
    """List current configuration values."""

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

    config = _get_user_config(is_global)
    flat_config = flatten_dict(config.to_dict())
    sorted_items = sorted(flat_config.items(), key=lambda x: x[0])

    # Create table
    table = Table(title="Configuration Values", border_style="blue", show_header=True, title_justify="center")
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

    # Group by prefix (before underscore)
    def get_prefix(item):
        return item[0].split("_")[0]

    for prefix, group in groupby(sorted_items, key=get_prefix):
        table.add_section()
        table.add_row(f"[bold yellow]{prefix.title()}[/bold yellow]", "")
        for key, value in group:
            table.add_row(f"  {key}", str(value))

    rich.print(table)


@config_command.command(name="get")
@click.argument("key")
@click.option("--global", "is_global", is_flag=True, help="Get the global configuration value")
def get_command(key: str, is_global: bool):
    """Get a configuration value."""
    config = _get_user_config(is_global)
    if not config.has_key(key):
        rich.print(f"[red]Error: Configuration key '{key}' not found[/red]")
        return

    value = config.get(key)

    rich.print(f"[cyan]{key}[/cyan]=[magenta]{value}[/magenta]")


@config_command.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--global", "is_global", is_flag=True, help="Sets the global configuration value")
def set_command(key: str, value: str, is_global: bool):
    """Set a configuration value and write to .env"""
    config = _get_user_config(is_global)
    if not config.has_key(key):
        rich.print(f"[red]Error: Configuration key '{key}' not found[/red]")
        return

    cur_value = config.get(key)
    if cur_value is None or cur_value.lower() != value.lower():
        try:
            config.set(key, value)
        except Exception as e:
            logging.exception(e)
            rich.print(f"[red]{e}[/red]")
            return

    rich.print(f"[green]Successfully set {key}=[magenta]{value}[/magenta] and saved to .env[/green]")


def _get_user_config(is_global: bool) -> UserConfig:
    if is_global or (active_session_path := session_manager.get_active_session()) is None:
        env_filepath = GLOBAL_ENV_FILE
    else:
        env_filepath = active_session_path / CODEGEN_DIR_NAME / ENV_FILENAME

    return UserConfig(env_filepath)
