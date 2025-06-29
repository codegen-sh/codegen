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

# Add commands to the main app
main.add_typer(init_command, name="init")
main.add_typer(logout_command, name="logout")
main.add_typer(login_command, name="login")
main.add_typer(profile_command, name="profile")
main.add_typer(style_debug_command, name="style-debug")
main.add_typer(update_command, name="update")
main.add_typer(config_command, name="config")


if __name__ == "__main__":
    main()
