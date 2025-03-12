import sys
from pathlib import Path

import rich
import rich_click as click

from codegen.cli.auth.session import CodegenSession
from codegen.cli.commands.init.render import get_success_message
from codegen.cli.rich.codeblocks import format_command
from codegen.cli.workspace.initialize_workspace import initialize_codegen
from codegen.shared.path import get_git_root_path


@click.command(name="init")
@click.option("--path", type=str, help="Path within a git repository. Defaults to the current directory.")
@click.option("--token", type=str, help="Access token for the git repository. Required for full functionality.")
@click.option("--language", type=click.Choice(["python", "typescript"], case_sensitive=False), help="Override automatic language detection")
@click.option("--fetch-docs", is_flag=True, help="Fetch docs and examples (requires auth)")
def init_command(path: str | None = None, token: str | None = None, language: str | None = None, fetch_docs: bool = False):
    """Initialize or update the Codegen folder."""
    # Print a message if not in a git repo
    path = Path.cwd() if path is None else Path(path)
    repo_path = get_git_root_path(path)
    rich.print(f"Found git repository at: {repo_path}")

    if repo_path is None:
        rich.print(f"\n[bold red]Error:[/bold red] Path={path} is not in a git repository")
        rich.print("[white]Please run this command from within a git repository.[/white]")
        rich.print("\n[dim]To initialize a new git repository:[/dim]")
        rich.print(format_command("git init"))
        rich.print(format_command("codegen init"))
        sys.exit(1)

    session = CodegenSession(repo_path=repo_path, git_token=token)
    if language:
        session.config.repository.language = language.upper()
        session.config.save()

    action = "Updating" if session.existing else "Initializing"
    codegen_dir, docs_dir, examples_dir = initialize_codegen(status=action, session=session, fetch_docs=fetch_docs)

    # Print success message
    rich.print(f"✅ {action} complete\n")
    rich.print(get_success_message(codegen_dir, docs_dir, examples_dir))

    # Print next steps
    rich.print("\n[bold]What's next?[/bold]\n")
    rich.print("1. Create a function:")
    rich.print(format_command('codegen create my-function -d "describe what you want to do"'))
    rich.print("2. Run it:")
    rich.print(format_command("codegen run my-function --apply-local"))
