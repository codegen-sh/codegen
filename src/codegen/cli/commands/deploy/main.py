import time
from pathlib import Path

import rich
import rich_click as click

from codegen.cli.api.client import RestAPI
from codegen.cli.auth.decorators import requires_auth
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.rich.codeblocks import format_command
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.codemod_manager import CodemodManager
from codegen.cli.utils.function_finder import DecoratedFunction


def deploy_functions(functions: list[DecoratedFunction], message: str | None = None) -> None:
    """Deploy a list of functions."""
    if not functions:
        rich.print("\n[yellow]No @codegen.function decorators found.[/yellow]\n")
        return

    # Deploy each function
    api_client = RestAPI(get_current_token())
    rich.print()  # Add a blank line before deployments

    for func in functions:
        with create_spinner(f"Deploying function '{func.name}'...") as status:
            start_time = time.time()
            response = api_client.deploy(
                codemod_name=func.name,
                codemod_source=func.source,
                lint_mode=func.lint_mode,
                lint_user_whitelist=func.lint_user_whitelist,
                message=message,
                arguments_schema=func.arguments_type_schema,
            )
            deploy_time = time.time() - start_time

        func_type = "Webhook" if func.lint_mode else "Function"
        rich.print(f"✅ {func_type} '{func.name}' deployed in {deploy_time:.3f}s! 🎉")
        rich.print("   [dim]View deployment:[/dim]")
        rich.print(format_command(f"codegen run {func.name}"))


@click.command(name="deploy")
@requires_auth
@click.argument("name", required=False)
@click.option("-d", "--directory", type=click.Path(exists=True, path_type=Path), help="Directory to search for functions")
@click.option("-m", "--message", help="Optional message to include with the deploy")
def deploy_command(name: str | None = None, directory: Path | None = None, message: str | None = None):
    """Deploy codegen functions.

    If NAME is provided, deploys a specific function by that name.
    If no NAME is provided, deploys all functions in the current directory or specified directory.
    """
    try:
        search_path = directory or Path.cwd()

        if name:
            # Find and deploy specific function by name
            functions = CodemodManager.get_decorated(search_path)
            matching = [f for f in functions if f.name == name]
            if not matching:
                msg = f"No function found with name '{name}'"
                raise click.ClickException(msg)
            if len(matching) > 1:
                # If multiple matches, show their locations
                rich.print(f"[yellow]Multiple functions found with name '{name}':[/yellow]")
                for func in matching:
                    rich.print(f"  • {func.filepath}")
                msg = "Please specify the exact directory with --directory"
                raise click.ClickException(msg)
            deploy_functions(matching, message=message)
        else:
            # Deploy all functions in the directory
            functions = CodemodManager.get_decorated(search_path)
            deploy_functions(functions)
    except Exception as e:
        msg = f"Failed to deploy: {e!s}"
        raise click.ClickException(msg)
