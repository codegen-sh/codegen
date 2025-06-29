import typer
from rich.traceback import install

from codegen import __version__

# Import config command (still a Typer app)
from codegen.cli.commands.config.main import config_command

# Import the actual command functions
from codegen.cli.commands.init.main import init
from codegen.cli.commands.login.main import login
from codegen.cli.commands.logout.main import logout
from codegen.cli.commands.mcp.main import mcp
from codegen.cli.commands.profile.main import profile
from codegen.cli.commands.style_debug.main import style_debug
from codegen.cli.commands.update.main import update

install(show_locals=True)


def version_callback(value: bool):
    """Print version and exit."""
    if value:
        print(__version__)
        raise typer.Exit()


# Create the main Typer app
main = typer.Typer(name="codegen", help="Codegen CLI - Transform your code with AI.", rich_markup_mode="rich")

# Add individual commands to the main app
main.command("init", help="Initialize or update the Codegen folder.")(init)
main.command("login", help="Store authentication token.")(login)
main.command("logout", help="Clear stored authentication token.")(logout)
main.command("mcp", help="Start the Codegen MCP server.")(mcp)
main.command("profile", help="Display information about the currently authenticated user.")(profile)
main.command("style-debug", help="Debug command to visualize CLI styling (spinners, etc).")(style_debug)
main.command("update", help="Update Codegen to the latest or specified version")(update)

# Config is a group, so add it as a typer
main.add_typer(config_command, name="config")


@main.callback()
def main_callback(version: bool = typer.Option(False, "--version", callback=version_callback, is_eager=True, help="Show version and exit")):
    """Codegen CLI - Transform your code with AI."""
    pass


if __name__ == "__main__":
    main()
