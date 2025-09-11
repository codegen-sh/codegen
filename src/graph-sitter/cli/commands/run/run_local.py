from pathlib import Path

import rich
import rich.progress
from rich.panel import Panel
from rich.status import Status

from codegen.sdk.cli.auth.session import CliSession
from codegen.sdk.cli.utils.function_finder import DecoratedFunction
from codegen.sdk.codebase.config import ProjectConfig
from codegen.sdk.codebase.progress.progress import Progress
from codegen.sdk.codebase.progress.task import Task
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.git.schemas.repo_config import RepoConfig
from codegen.sdk.git.utils.language import determine_project_language
from codegen.sdk.shared.enums.programming_language import ProgrammingLanguage


class RichTask(Task):
    _task: rich.progress.Task
    _progress: rich.progress.Progress
    _total: int | None

    def __init__(self, task: rich.progress.Task, progress: rich.progress.Progress, total: int | None = None) -> None:
        self._task = task
        self._progress = progress
        self._total = total

    def update(self, message: str, count: int | None = None) -> None:
        self._progress.update(self._task, description=message, completed=count)

    def end(self) -> None:
        self._progress.update(self._task, completed=self._total)


class RichProgress(Progress[RichTask]):
    _progress: rich.progress.Progress

    def __init__(self, progress: rich.progress.Progress) -> None:
        self._progress = progress

    def begin(self, message: str, count: int | None = None) -> RichTask:
        task = self._progress.add_task(description=message, total=count)
        return RichTask(task, progress=self._progress, total=count)


def parse_codebase(
    repo_path: Path,
    subdirectories: list[str] | None = None,
    language: ProgrammingLanguage | None = None,
) -> Codebase:
    """Parse the codebase at the given root.

    Args:
        repo_root: Path to the repository root

    Returns:
        Parsed Codebase object
    """
    with rich.progress.Progress(
        rich.progress.TextColumn("[progress.description]{task.description}"),
        rich.progress.BarColumn(bar_width=None),
        rich.progress.TaskProgressColumn(),
        rich.progress.TimeRemainingColumn(),
        rich.progress.TimeElapsedColumn(),
        expand=True,
    ) as progress:
        codebase = Codebase(
            projects=[
                ProjectConfig(
                    repo_operator=RepoOperator(repo_config=RepoConfig.from_repo_path(repo_path=repo_path)),
                    subdirectories=subdirectories,
                    programming_language=language or determine_project_language(repo_path),
                )
            ],
            progress=RichProgress(progress),
        )
    return codebase


def run_local(
    session: CliSession,
    function: DecoratedFunction,
    diff_preview: int | None = None,
) -> None:
    """Run a function locally against the codebase.

    Args:
        session: The current codegen session
        function: The function to run
        diff_preview: Number of lines of diff to preview (None for all)
    """
    rich.print(f"Parsing codebase at {session.repo_path} with subdirectories {function.subdirectories or 'ALL'} and language {function.language or 'AUTO'} ...")
    # Parse codebase and run
    codebase = parse_codebase(repo_path=session.repo_path, subdirectories=function.subdirectories, language=function.language)
    with Status("[bold]Running codemod...", spinner="dots") as status:
        status.update("")
        function.run(codebase)  # Run the function
        status.update("[bold green]✓ Completed codemod")

    # Get the diff from the codebase
    result = codebase.get_diff()

    # Handle no changes case
    if not result:
        rich.print("\n[yellow]No changes were produced by this codemod[/yellow]")
        return

    # Show diff preview if requested
    if diff_preview:
        rich.print("")  # Add spacing
        diff_lines = result.splitlines()
        truncated = len(diff_lines) > diff_preview
        limited_diff = "\n".join(diff_lines[:diff_preview])

        if truncated:
            limited_diff += f"\n\n...\n\n[yellow]diff truncated to {diff_preview} lines[/yellow]"

        panel = Panel(limited_diff, title="[bold]Diff Preview[/bold]", border_style="blue", padding=(1, 2), expand=False)
        rich.print(panel)

    # Apply changes
    rich.print("")
    rich.print("[green]✓ Changes have been applied to your local filesystem[/green]")
