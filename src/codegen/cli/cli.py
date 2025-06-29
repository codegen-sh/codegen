import rich_click as click
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


@click.group(name="codegen")
@click.version_option(prog_name="codegen", message="%(version)s")
def main():
    """Codegen CLI - Transform your code with AI."""
    pass


# Add commands to the main group
main.add_command(init_command)
main.add_command(logout_command)
main.add_command(login_command)
main.add_command(profile_command)
main.add_command(style_debug_command)
main.add_command(update_command)
main.add_command(config_command)


if __name__ == "__main__":
    main()
