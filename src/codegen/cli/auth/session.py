from pathlib import Path

import click
import rich
from github import BadCredentialsException
from github.MainClass import Github

from codegen.cli.git.repo import get_git_repo
from codegen.cli.rich.codeblocks import format_command
from codegen.configs.constants import CODEGEN_DIR_NAME, ENV_FILENAME
from codegen.configs.session_manager import session_manager
from codegen.configs.user_config import UserConfig
from codegen.git.repo_operator.local_git_repo import LocalGitRepo


class CodegenSession:
    """Represents an authenticated codegen session with user and repository context"""

    repo_path: Path
    local_git: LocalGitRepo
    codegen_dir: Path
    config: UserConfig
    existing: bool

    def __init__(self, repo_path: Path, git_token: str | None = None) -> None:
        if not repo_path.exists() or get_git_repo(repo_path) is None:
            rich.print(f"\n[bold red]Error:[/bold red] Path to git repo does not exist at {self.repo_path}")
            raise click.Abort()

        self.repo_path = repo_path
        self.local_git = LocalGitRepo(repo_path=repo_path)
        self.codegen_dir = repo_path / CODEGEN_DIR_NAME
        self.config = UserConfig(env_filepath=repo_path / ENV_FILENAME)
        self.config.secrets.github_token = git_token or self.config.secrets.github_token
        self.existing = session_manager.get_session(repo_path) is not None

        self._initialize()
        session_manager.set_active_session(repo_path)

    @classmethod
    def from_active_session(cls) -> "CodegenSession | None":
        active_session = session_manager.get_active_session()
        if not active_session:
            return None

        return cls(active_session)

    def _initialize(self) -> None:
        """Initialize the codegen session"""
        self._validate()

        self.config.repository.path = self.config.repository.path or str(self.local_git.repo_path)
        self.config.repository.owner = self.config.repository.owner or self.local_git.owner
        self.config.repository.user_name = self.config.repository.user_name or self.local_git.user_name
        self.config.repository.user_email = self.config.repository.user_email or self.local_git.user_email
        self.config.repository.language = self.config.repository.language or self.local_git.get_language(access_token=self.config.secrets.github_token).upper()
        self.config.save()

    def _validate(self) -> None:
        """Validates that the session configuration is correct, otherwise raises an error"""
        if not self.codegen_dir.exists():
            self.codegen_dir.mkdir(parents=True, exist_ok=True)

        git_token = self.config.secrets.github_token
        if git_token is None:
            rich.print("\n[bold yellow]Warning:[/bold yellow] GitHub token not found")
            rich.print("To enable full functionality, please set your GitHub token:")
            rich.print(format_command("export GITHUB_TOKEN=<your-token>"))
            rich.print("Or pass in as a parameter:")
            rich.print(format_command("codegen init --token <your-token>"))

        if self.local_git.origin_remote is None:
            rich.print("\n[bold yellow]Warning:[/bold yellow] No remote found for repository")
            rich.print("[white]To enable full functionality, please add a remote to the repository[/white]")
            rich.print("\n[dim]To add a remote to the repository:[/dim]")
            rich.print(format_command("git remote add origin <your-repo-url>"))

        try:
            if git_token is not None:
                Github(login_or_token=git_token).get_repo(self.local_git.full_name)
        except BadCredentialsException:
            rich.print(format_command(f"\n[bold red]Error:[/bold red] Invalid GitHub token={git_token} for repo={self.local_git.full_name}"))
            rich.print("[white]Please provide a valid GitHub token for this repository.[/white]")
            raise click.Abort()

    def __str__(self) -> str:
        return f"CodegenSession(user={self.config.repository.user_name}, repo={self.config.repository.repo_name})"
