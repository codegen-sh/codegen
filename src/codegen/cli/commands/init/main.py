from pathlib import Path

import rich
import typer

from codegen.cli.auth.session import CodegenSession
from codegen.cli.rich.codeblocks import format_command
from codegen.shared.logging.get_logger import get_logger
from codegen.shared.path import get_git_root_path

# Initialize logger
logger = get_logger(__name__)


def init(
    path: str | None = typer.Option(None, help="Path within a git repository. Defaults to the current directory."),
    token: str | None = typer.Option(None, help="Access token for the git repository. Required for full functionality."),
    language: str | None = typer.Option(None, help="Override automatic language detection (python or typescript)"),
    fetch_docs: bool = typer.Option(False, "--fetch-docs", help="Fetch docs and examples (requires auth)"),
):
    """Initialize or update the Codegen folder."""
    logger.info("Init command started", extra={"operation": "init", "path": path, "language": language, "fetch_docs": fetch_docs, "has_token": bool(token)})

    # Validate language option
    if language and language.lower() not in ["python", "typescript"]:
        logger.error("Invalid language specified", extra={"operation": "init", "language": language, "error_type": "invalid_language"})
        rich.print(f"[bold red]Error:[/bold red] Invalid language '{language}'. Must be 'python' or 'typescript'.")
        raise typer.Exit(1)

    # Print a message if not in a git repo
    path_obj = Path.cwd() if path is None else Path(path)
    repo_path = get_git_root_path(path_obj)
    rich.print(f"Found git repository at: {repo_path}")

    if repo_path is None:
        logger.error("Not in a git repository", extra={"operation": "init", "path": str(path_obj), "error_type": "not_git_repo"})
        rich.print(f"\n[bold red]Error:[/bold red] Path={path_obj} is not in a git repository")
        rich.print("[white]Please run this command from within a git repository.[/white]")
        rich.print("\n[dim]To initialize a new git repository:[/dim]")
        rich.print(format_command("git init"))
        rich.print(format_command("codegen init"))
        raise typer.Exit(1)

    # At this point, repo_path is guaranteed to be not None
    assert repo_path is not None

    # Session creation details not needed in logs

    session = CodegenSession(repo_path=repo_path, git_token=token)
    if language:
        session.config.repository.language = language.upper()
        session.config.save()
        # Language override details included in completion log

    action = "Updating" if session.existing else "Initializing"

    logger.info(
        "Codegen session created",
        extra={"operation": "init", "repo_path": str(repo_path), "action": action.lower(), "existing": session.existing, "language": getattr(session.config.repository, "language", None)},
    )

    # Create the codegen directory
    codegen_dir = session.codegen_dir
    codegen_dir.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Init completed successfully",
        extra={
            "operation": "init",
            "repo_path": str(repo_path),
            "codegen_dir": str(codegen_dir),
            "action": action.lower(),
            "language": getattr(session.config.repository, "language", None),
            "fetch_docs": fetch_docs,
        },
    )

    # Print success message
    rich.print(f"✅ {action} complete\n")
    rich.print(f"Codegen workspace initialized at: [bold]{codegen_dir}[/bold]")

    # Print next steps
    rich.print("\n[bold]What's next?[/bold]\n")
    rich.print("1. Create a function:")
    rich.print(format_command('codegen create my-function . -d "describe what you want to do"'))
    rich.print("2. Run it:")
    rich.print(format_command("codegen run my-function --apply-local"))
