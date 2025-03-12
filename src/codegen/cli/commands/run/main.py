import json
import os

import rich_click as click

from codegen.cli.auth.session import CodegenSession
from codegen.cli.utils.codemod_manager import CodemodManager
from codegen.cli.utils.json_schema import validate_json
from codegen.cli.workspace.decorators import requires_init
from codegen.cli.workspace.venv_manager import VenvManager


@click.command(name="run")
@requires_init
@click.argument("label", required=True)
@click.option("--web", is_flag=True, help="Run the function on the web service instead of locally")
@click.option("--daemon", "-d", is_flag=True, help="Run the function against a running daemon")
@click.option("--diff-preview", type=int, help="Show a preview of the first N lines of the diff")
@click.option("--arguments", type=str, help="Arguments as a json string to pass as the function's 'arguments' parameter")
def run_command(
    session: CodegenSession,
    label: str,
    web: bool = False,
    daemon: bool = False,
    diff_preview: int | None = None,
    arguments: str | None = None,
):
    """Run a codegen function by its label."""
    if web and daemon:
        msg = "Cannot enable run on both the web and daemon"
        raise ValueError(msg)

    # Ensure venv is initialized
    venv = VenvManager(session.codegen_dir)
    if not venv.is_initialized():
        msg = "Virtual environment not found. Please run 'codegen init' first."
        raise click.ClickException(msg)

    # Set up environment with venv
    os.environ["VIRTUAL_ENV"] = str(venv.venv_dir)
    os.environ["PATH"] = f"{venv.venv_dir}/bin:{os.environ['PATH']}"

    # Get and validate the codemod
    codemod = CodemodManager.get_codemod(label)

    # Handle arguments if needed
    if codemod.arguments_type_schema and not arguments:
        msg = f"This function requires the --arguments parameter. Expected schema: {codemod.arguments_type_schema}"
        raise click.ClickException(msg)

    if codemod.arguments_type_schema and arguments:
        arguments_json = json.loads(arguments)
        is_valid = validate_json(codemod.arguments_type_schema, arguments_json)
        if not is_valid:
            msg = f"Invalid arguments format. Expected schema: {codemod.arguments_type_schema}"
            raise click.ClickException(msg)

    # Run the codemod
    if web:
        from codegen.cli.commands.run.run_cloud import run_cloud

        run_cloud(session, codemod, diff_preview=diff_preview)
    elif daemon:
        from codegen.cli.commands.run.run_daemon import run_daemon

        run_daemon(session, codemod, diff_preview=diff_preview)
    else:
        from codegen.cli.commands.run.run_local import run_local

        run_local(session, codemod, diff_preview=diff_preview)
