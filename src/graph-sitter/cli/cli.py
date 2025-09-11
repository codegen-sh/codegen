import rich_click as click
from rich.traceback import install

# Removed reference to non-existent agent module
from codegen.sdk.cli.commands.config.main import config_command
from codegen.sdk.cli.commands.create.main import create_command
from codegen.sdk.cli.commands.init.main import init_command
from codegen.sdk.cli.commands.list.main import list_command
from codegen.sdk.cli.commands.lsp.lsp import lsp_command
from codegen.sdk.cli.commands.notebook.main import notebook_command
from codegen.sdk.cli.commands.reset.main import reset_command
from codegen.sdk.cli.commands.run.main import run_command
from codegen.sdk.cli.commands.start.main import start_command
from codegen.sdk.cli.commands.style_debug.main import style_debug_command
from codegen.sdk.cli.commands.update.main import update_command

click.rich_click.USE_RICH_MARKUP = True
install(show_locals=True)


@click.group()
@click.version_option(prog_name="codegen", message="%(version)s")
def main():
    """codegen.sdk.cli - Transform your code with AI."""


# Wrap commands with error handler
# Removed reference to non-existent agent_command
main.add_command(init_command)
main.add_command(run_command)
main.add_command(create_command)
main.add_command(list_command)
main.add_command(style_debug_command)
main.add_command(notebook_command)
main.add_command(reset_command)
main.add_command(update_command)
main.add_command(config_command)
main.add_command(lsp_command)
main.add_command(start_command)


if __name__ == "__main__":
    main()
