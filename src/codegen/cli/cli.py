import typer
from rich.traceback import install

# Removed reference to non-existent agent module
from codegen.cli.commands.config.main import config_command
from codegen.cli.commands.init.main import init_command
from codegen.cli.commands.login.main import login_command
from codegen.cli.commands.logout.main import logout_command
from codegen.cli.commands.profile.main import profile_command
from codegen.cli.commands.style_debug.main import style_debug_command
from codegen.cli.commands.update.main import update_command

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
main.command("init")(init)
main.command("login")(login)
main.command("logout")(logout)
main.command("profile")(profile)
main.command("style-debug")(style_debug)
main.command("update")(update)

# Config is a group, so add it as a typer
main.add_typer(config_command, name="config")


if __name__ == "__main__":
    main()
