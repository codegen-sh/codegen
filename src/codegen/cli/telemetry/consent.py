"""Telemetry consent management for the CLI."""

import uuid
from pathlib import Path

import rich
import typer

from codegen.configs.constants import GLOBAL_ENV_FILE
from codegen.configs.models.telemetry import TelemetryConfig


def prompt_telemetry_consent() -> bool:
    """Prompt user for telemetry consent during first-time setup.

    Returns:
        bool: True if user consents to telemetry, False otherwise
    """
    # Display Codegen header
    print("\033[38;2;82;19;217m" + "/" * 20 + " Codegen\033[0m")
    print()

    rich.print("[bold]📊 Help Improve Codegen CLI[/bold]")
    rich.print(
        "We'd like to collect anonymous usage data to improve the CLI experience.\n"
        "This includes:\n"
        "  • Command usage patterns\n"
        "  • Performance metrics\n"
        "  • Error diagnostics (no source code or PII)\n"
        "  • CLI version and platform info\n"
    )
    rich.print("[dim]You can change this setting anytime with 'codegen config telemetry'[/dim]\n")

    consent = typer.confirm("Enable anonymous telemetry?", default=False)
    return consent


def ensure_telemetry_consent() -> TelemetryConfig:
    """Ensure telemetry consent has been obtained and configured.

    This function:
    1. Loads existing telemetry config
    2. If not previously prompted, asks for consent
    3. Saves the configuration

    Returns:
        TelemetryConfig: The telemetry configuration
    """
    # Load telemetry config (uses global config file)
    telemetry = TelemetryConfig(env_filepath=GLOBAL_ENV_FILE)

    # If already prompted, return existing config
    if telemetry.consent_prompted:
        return telemetry

    # Prompt for consent
    consent = prompt_telemetry_consent()

    # Update configuration
    telemetry.enabled = consent
    telemetry.consent_prompted = True

    if consent:
        rich.print("[green]✓ Telemetry enabled. Thank you for helping improve Codegen![/green]")
    else:
        rich.print("[yellow]✓ Telemetry disabled. You can enable it later with 'codegen config telemetry'[/yellow]")

    # Save to global config
    telemetry.write_to_file(GLOBAL_ENV_FILE)

    # Refresh logging configuration to apply the new settings
    try:
        from codegen.shared.logging.get_logger import refresh_telemetry_config

        refresh_telemetry_config()
    except ImportError:
        pass  # Logging refresh not available

    return telemetry


def update_telemetry_consent(enabled: bool) -> None:
    """Update telemetry consent preference.

    Args:
        enabled: Whether to enable telemetry
    """
    telemetry = TelemetryConfig(env_filepath=GLOBAL_ENV_FILE)
    telemetry.enabled = enabled
    telemetry.consent_prompted = True

    telemetry.write_to_file(GLOBAL_ENV_FILE)

    # Refresh logging configuration to apply the new settings
    try:
        from codegen.shared.logging.get_logger import refresh_telemetry_config

        refresh_telemetry_config()
    except ImportError:
        pass  # Logging refresh not available

    if enabled:
        rich.print("[green]✓ Telemetry enabled[/green]")
    else:
        rich.print("[yellow]✓ Telemetry disabled[/yellow]")
