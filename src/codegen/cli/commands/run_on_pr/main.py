import rich
import rich_click as click

from codegen.cli.api.client import RestAPI
from codegen.cli.auth.decorators import requires_auth
from codegen.cli.auth.session import CodegenSession
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.codemod_manager import CodemodManager


def run_on_pr(session: CodegenSession, codemod_name: str, pr_number: int) -> None:
    """Test a webhook against a specific PR."""
    # Find the codemod
    codemod = CodemodManager.get(codemod_name)
    if not codemod:
        msg = f"No function found with name '{codemod_name}'"
        raise click.ClickException(msg)

    with create_spinner(f"Testing webhook '{codemod_name}' on PR #{pr_number}...") as status:
        try:
            response = RestAPI(get_current_token()).run_on_pr(
                codemod_name=codemod_name,
                repo_full_name=session.config.repository.full_name,
                github_pr_number=pr_number,
            )
            status.stop()
            rich.print(f"✅ Webhook test completed for PR #{pr_number}")
            rich.print(f"   [dim]View results:[/dim] [blue underline]{response.web_url}[/blue underline]")
        except Exception as e:
            status.stop()
            msg = f"Failed to test webhook: {e!s}"
            raise click.ClickException(msg)


@click.command(name="run-on-pr")
@requires_auth
@click.argument("codemod_name", type=str)
@click.argument("pr_number", type=int)
def run_on_pr_command(session: CodegenSession, codemod_name: str, pr_number: int):
    """Test a webhook against a specific PR.

    CODEMOD_NAME is the name of the codemod to test
    PR_NUMBER is the GitHub PR number to test against
    """
    run_on_pr(session, codemod_name, pr_number)
