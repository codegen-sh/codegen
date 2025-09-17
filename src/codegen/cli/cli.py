import atexit

import typer
from rich.traceback import install

from codegen import __version__
from codegen.cli.commands.agent.main import agent
from codegen.cli.commands.agents.main import agents_app
from codegen.cli.commands.claude.main import claude
from codegen.cli.commands.config.main import config_command
from codegen.cli.commands.init.main import init
from codegen.cli.commands.integrations.main import integrations_app
from codegen.cli.commands.login.main import login
from codegen.cli.commands.logout.main import logout
from codegen.cli.commands.org.main import org
from codegen.cli.commands.profile.main import profile_app
from codegen.cli.commands.repo.main import repo
from codegen.cli.commands.tui.main import tui
from codegen.cli.commands.update.main import update
from codegen.shared.logging.get_logger import get_logger

# Initialize logger for CLI command tracking
logger = get_logger(__name__)

# Set up global exception logging early
try:
    from codegen.cli.telemetry.exception_logger import setup_global_exception_logging

    setup_global_exception_logging()
except ImportError:
    # Exception logging dependencies not available - continue without it
    pass


install(show_locals=True)

# Register telemetry shutdown on exit
try:
    from codegen.cli.telemetry.exception_logger import teardown_global_exception_logging
    from codegen.cli.telemetry.otel_setup import shutdown_otel_logging

    atexit.register(shutdown_otel_logging)
    atexit.register(teardown_global_exception_logging)
except ImportError:
    # OTel dependencies not available
    pass


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        logger.info("Version command invoked", extra={"operation": "cli.version", "version": __version__})
        print(__version__)
        raise typer.Exit()


# Create the main Typer app
main = typer.Typer(name="codegen", help="Codegen - the Operating System for Code Agents.", rich_markup_mode="rich")

# Check for updates on startup (non-blocking)
try:
    # Only check when no arguments are passed (just "codegen" to launch TUI)
    import sys

    from codegen.cli.commands.update import check_for_updates_on_startup

    if len(sys.argv) == 1:
        check_for_updates_on_startup()
except ImportError:
    pass  # Update check dependencies not available

# Add individual commands to the main app (logging now handled within each command)
main.command("agent", help="Create a new agent run with a prompt.")(agent)
main.command("claude", help="Run Claude Code with OpenTelemetry monitoring and logging.")(claude)
main.command("init", help="Initialize or update the Codegen folder.")(init)
main.command("login", help="Store authentication token.")(login)
main.command("logout", help="Clear stored authentication token.")(logout)
main.command("org", help="Manage and switch between organizations.")(org)
main.command("repo", help="Manage repository configuration and environment variables.")(repo)
main.command("tui", help="Launch the interactive TUI interface.")(tui)
main.command("update", help="Update Codegen to the latest or specified version")(update)

# Add Typer apps as sub-applications (these will handle their own sub-command logging)
main.add_typer(agents_app, name="agents")
main.add_typer(config_command, name="config")
main.add_typer(integrations_app, name="integrations")
main.add_typer(profile_app, name="profile")


@main.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context, version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True, help="Show version and exit")):
    """Codegen - the Operating System for Code Agents"""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, launch TUI
        logger.info("CLI launched without subcommand - starting TUI", extra={"operation": "cli.main", "action": "default_tui_launch", "command": "codegen"})
        from codegen.cli.tui.app import run_tui

        run_tui()
    else:
        # Log when a subcommand is being invoked
        logger.debug("CLI main callback with subcommand", extra={"operation": "cli.main", "subcommand": ctx.invoked_subcommand, "command": f"codegen {ctx.invoked_subcommand}"})


if __name__ == "__main__":
    main()
