import logging

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
    table = Table(title="Configuration Values", border_style="blue", show_header=True)
    table.add_column("Key", style="cyan", no_wrap=True)
    table.add_column("Value", style="magenta")

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

    for key, value in sorted_items:
        table.add_row(key, str(value))

    rich.print(table)


@config_command.command(name="get")
@click.argument("key")
@click.option("--global", "is_global", is_flag=True, help="Get the global configuration value")
def get_command(key: str, is_global: bool):
    """Get a configuration value."""
    config = _get_user_config(is_global)
    value = config.get(key)
    if value is None:
        rich.print(f"[red]Error: Configuration key '{key}' not found[/red]")
        return

    rich.print(f"[cyan]{key}[/cyan] = [magenta]{value}[/magenta]")


@config_command.command(name="set")
@click.argument("key")
@click.argument("value")
@click.option("--global", "is_global", is_flag=True, help="Sets the global configuration value")
def set_command(key: str, value: str, is_global: bool):
    """Set a configuration value and write to config.toml."""
    config = _get_user_config(is_global)
    cur_value = config.get(key)
    if cur_value is None:
        rich.print(f"[red]Error: Configuration key '{key}' not found[/red]")
        return

    if cur_value.lower() != value.lower():
        try:
            config.set(key, value)
        except Exception as e:
            logging.exception(e)
            rich.print(f"[red]{e}[/red]")
            return

    rich.print(f"[green]Successfully set {key}=[magenta]{value}[/magenta] and saved to config.toml[/green]")


def _get_user_config(is_global: bool) -> UserConfig:
    if is_global or (active_session_path := session_manager.get_active_session()) is None:
        env_filepath = GLOBAL_ENV_FILE
    else:
        env_filepath = active_session_path / CODEGEN_DIR_NAME / ENV_FILENAME

    user_config = UserConfig(env_filepath)
    print(f"Returning user config from config!!!: {user_config} with env_filepath: {env_filepath}")
    return user_config
