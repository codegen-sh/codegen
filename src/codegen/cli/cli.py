import typer
from rich.traceback import install

# Import config command (still a Typer app)
from codegen.cli.commands.config.main import config_command

install(show_locals=True)

# Create the main Typer app
main = typer.Typer(
    name="codegen",
    help="Codegen CLI - Transform your code with AI.",
    rich_markup_mode="rich"
)

# Import the actual command functions
from codegen.cli.commands.init.main import init
from codegen.cli.commands.login.main import login
from codegen.cli.commands.logout.main import logout
from codegen.cli.commands.profile.main import profile
from codegen.cli.commands.style_debug.main import style_debug
from codegen.cli.commands.update.main import update

# Add individual commands to the main app
main.command("init", help="Initialize or update the Codegen folder.")(init)
main.command("login", help="Store authentication token.")(login)
main.command("logout", help="Clear stored authentication token.")(logout)
main.command("profile", help="Display information about the currently authenticated user.")(profile)
main.command("style-debug", help="Debug command to visualize CLI styling (spinners, etc).")(style_debug)
main.command("update", help="Update Codegen to the latest or specified version")(update)

# Config is a group, so add it as a typer
main.add_typer(config_command, name="config")


if __name__ == "__main__":
    main()
