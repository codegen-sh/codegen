import logging

import rich
import rich_click as click
from rich.table import Table

from codegen.configs.constants import ENV_FILENAME, GLOBAL_ENV_FILE
from codegen.configs.user_config import UserConfig
from codegen.shared.path import get_git_root_path


@click.group(name="config")
def config_command():
    """Manage codegen configuration."""
    pass


@config_command.command(name="list")
def list_command():
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
@click.argument("key")
def get_command(key: str):
    """Get a configuration value."""
    config = _get_user_config()
    if not config.has_key(key):
        rich.print(f"[red]Error: Configuration key '{key}' not found[/red]")
        return

    value = config.get(key)

    rich.print(f"[cyan]{key}[/cyan]=[magenta]{value}[/magenta]")


@config_command.command(name="set")
@click.argument("key")
@click.argument("value")
def set_command(key: str, value: str):
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
