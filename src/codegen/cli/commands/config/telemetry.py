"""Telemetry configuration commands."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from codegen.cli.telemetry import update_telemetry_consent
from codegen.configs.constants import GLOBAL_CONFIG_DIR, GLOBAL_ENV_FILE
from codegen.configs.models.telemetry import TelemetryConfig

console = Console()

# Create the telemetry sub-app
telemetry_app = typer.Typer(help="Manage telemetry settings")


@telemetry_app.command()
def enable():
    """Enable telemetry data collection."""
    update_telemetry_consent(enabled=True)


@telemetry_app.command()
def disable():
    """Disable telemetry data collection."""
    update_telemetry_consent(enabled=False)


@telemetry_app.command()
def status():
    """Show current telemetry settings."""
    telemetry = TelemetryConfig(env_filepath=GLOBAL_ENV_FILE)

    table = Table(title="Telemetry Settings", show_header=False)
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")

    table.add_row("Enabled", "✅ Yes" if telemetry.enabled else "❌ No")
    table.add_row("Debug Mode", "Yes" if telemetry.debug else "No")

    console.print(table)
    console.print("\n[dim]Telemetry helps us improve the CLI experience.[/dim]")
    console.print("[dim]No personal information or source code is collected.[/dim]")


@telemetry_app.command()
def debug(
    enable: bool = typer.Option(None, "--enable/--disable", help="Enable or disable debug mode"),
    show_logs: bool = typer.Option(False, "--logs", help="Show recent debug logs"),
    clear: bool = typer.Option(False, "--clear", help="Clear debug logs"),
):
    """Manage telemetry debug mode and logs."""
    telemetry = TelemetryConfig(env_filepath=GLOBAL_ENV_FILE)
    debug_dir = GLOBAL_CONFIG_DIR / "telemetry_debug"

    # Handle enable/disable
    if enable is not None:
        telemetry.debug = enable
        telemetry.write_to_file(GLOBAL_ENV_FILE)

        # Refresh logging configuration to immediately apply the debug mode change
        try:
            from codegen.shared.logging.get_logger import refresh_telemetry_config

            refresh_telemetry_config()
        except ImportError:
            pass  # Logging refresh not available

        console.print(f"[green]✓ Debug mode {'enabled' if enable else 'disabled'}[/green]")
        if enable:
            console.print(f"[dim]Debug logs will be written to: {debug_dir}[/dim]")
            console.print("[dim]Console logging will now be enabled for all CLI operations[/dim]")
        else:
            console.print("[dim]Console logging will now be disabled for CLI operations[/dim]")

    # Handle clear
    if clear:
        if debug_dir.exists():
            import shutil

            shutil.rmtree(debug_dir)
            console.print("[green]✓ Debug logs cleared[/green]")
        else:
            console.print("[yellow]No debug logs to clear[/yellow]")
        return

    # Handle show logs
    if show_logs:
        if not debug_dir.exists():
            console.print("[yellow]No debug logs found[/yellow]")
            return

        # Find most recent session file
        session_files = sorted(debug_dir.glob("session_*.jsonl"), reverse=True)
        if not session_files:
            console.print("[yellow]No debug sessions found[/yellow]")
            return

        latest_file = session_files[0]
        console.print(f"\n[cyan]Latest session:[/cyan] {latest_file.name}")

        # Read and display spans
        with open(latest_file) as f:
            spans = []
            for line in f:
                data = json.loads(line)
                if data["type"] == "span":
                    spans.append(data)

        if not spans:
            console.print("[yellow]No spans recorded in this session[/yellow]")
            return

        # Create table
        table = Table(title=f"Telemetry Spans ({len(spans)} total)")
        table.add_column("Operation", style="cyan")
        table.add_column("Duration (ms)", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("Key Attributes", style="white")

        for span in spans[-10:]:  # Show last 10 spans
            duration = f"{span.get('duration_ms', 0):.2f}" if span.get("duration_ms") else "N/A"
            status = span["status"]["status_code"]

            # Extract key attributes
            attrs = span.get("attributes", {})
            key_attrs = []
            for key in ["cli.command.name", "cli.operation.name", "event.name"]:
                if key in attrs:
                    key_attrs.append(f"{key.split('.')[-1]}: {attrs[key]}")

            table.add_row(span["name"], duration, status, "\n".join(key_attrs[:2]) if key_attrs else "")

        console.print(table)
        console.print(f"\n[dim]Full logs available at: {latest_file}[/dim]")

    # If no action specified, show current status
    if enable is None and not show_logs and not clear:
        console.print(f"Debug mode: {'[green]Enabled[/green]' if telemetry.debug else '[red]Disabled[/red]'}")
        if debug_dir.exists():
            log_count = len(list(debug_dir.glob("session_*.jsonl")))
            console.print(f"Debug sessions: {log_count}")
            console.print(f"Debug directory: {debug_dir}")


@telemetry_app.callback(invoke_without_command=True)
def telemetry_callback(ctx: typer.Context):
    """Manage telemetry settings."""
    if ctx.invoked_subcommand is None:
        # If no subcommand is provided, show status
        status()
