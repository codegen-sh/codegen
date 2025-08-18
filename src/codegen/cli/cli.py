import typer
from rich.traceback import install

from codegen import __version__

# Import config command (still a Typer app)
from codegen.cli.commands.agent.main import agent
from codegen.cli.commands.agents.main import agents_app

# Import the actual command functions
from codegen.cli.commands.claude.main import claude
from codegen.cli.commands.config.main import config_command
from codegen.cli.commands.init.main import init
from codegen.cli.commands.integrations.main import integrations_app
from codegen.cli.commands.login.main import login
from codegen.cli.commands.logout.main import logout
from codegen.cli.commands.org.main import org
from codegen.cli.commands.profile.main import profile_app
from codegen.cli.commands.repo.main import repo
from codegen.cli.commands.style_debug.main import style_debug
from codegen.cli.commands.tools.main import tools
from codegen.cli.commands.tui.main import tui
from codegen.cli.commands.update.main import update

install(show_locals=True)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        print(__version__)
        raise typer.Exit()


# Create the main Typer app
main = typer.Typer(name="codegen", help="Codegen - the Operating System for Code Agents.", rich_markup_mode="rich")

# Add individual commands to the main app
main.command("agent", help="Create a new agent run with a prompt.")(agent)
main.command("claude", help="Run Claude Code with OpenTelemetry monitoring and logging.")(claude)
main.command("init", help="Initialize or update the Codegen folder.")(init)
main.command("login", help="Store authentication token.")(login)
main.command("logout", help="Clear stored authentication token.")(logout)
main.command("org", help="Manage and switch between organizations.")(org)
# Profile is now a Typer app
main.command("repo", help="Manage repository configuration and environment variables.")(repo)
main.command("style-debug", help="Debug command to visualize CLI styling (spinners, etc).")(style_debug)
main.command("tools", help="List available tools from the Codegen API.")(tools)
main.command("tui", help="Launch the interactive TUI interface.")(tui)
main.command("update", help="Update Codegen to the latest or specified version")(update)

# Add Typer apps as sub-applications
main.add_typer(agents_app, name="agents")
main.add_typer(config_command, name="config")
main.add_typer(integrations_app, name="integrations")
main.add_typer(profile_app, name="profile")


@main.callback(invoke_without_command=True)
def main_callback(ctx: typer.Context, version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True, help="Show version and exit")):
    """Codegen - the Operating System for Code Agents"""
    if ctx.invoked_subcommand is None:
        # No subcommand provided, launch TUI
        from codegen.cli.tui.app import run_tui

        run_tui()


if __name__ == "__main__":
    main()
