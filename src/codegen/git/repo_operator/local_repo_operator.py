import logging
import os
from typing import override

from git import Repo as GitCLI
from github.PullRequest import PullRequest

from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.repo_operator.local_git_repo import LocalGitRepo
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import FetchResult
from codegen.git.schemas.repo_config import RepoConfig

logger = logging.getLogger(__name__)


class OperatorIsLocal(Exception):
    """Error raised while trying to do a remote operation on a local operator"""


class LocalRepoOperator(RepoOperator):
    """RepoOperator that does not depend on remote Github.
    It is useful for:
    - Testing codemods locally with a repo already cloned from Github on disk.
    - Creating "fake" repos from a dictionary of files contents
    """

    _local_git_repo: LocalGitRepo

    def __init__(
        self,
        repo_config: RepoConfig,
        access_token: str | None = None,
        bot_commit: bool = False,
    ) -> None:
        super().__init__(repo_config=repo_config, access_token=access_token, bot_commit=bot_commit)
        os.makedirs(self.repo_path, exist_ok=True)
        GitCLI.init(self.repo_path)
        self._local_git_repo = LocalGitRepo(repo_path=repo_config.repo_path)
        if repo_config.full_name is None:
            repo_config.full_name = self._local_git_repo.full_name

    ####################################################################################################################
    # PROPERTIES
    ####################################################################################################################

    @property
    def remote_git_repo(self) -> GitRepoClient | None:
        """Get the remote GitRepoClient object for the current local repo."""
        if not self.access_token:
            msg = "Must initialize with access_token to get remote"
            raise ValueError(msg)

        if not self._local_git_repo.has_remote():
            msg = "Cannot initialize remote GitRepoClient from local Git"
            raise ValueError(msg)

        return super().remote_git_repo

    ####################################################################################################################
    # CLASS METHODS
    ####################################################################################################################

    ####################################################################################################################
    # PROPERTIES
    ####################################################################################################################

    @override
    def pull_repo(self) -> None:
        """Pull the latest commit down to an existing local repo"""
        raise OperatorIsLocal()

    def fetch_remote(self, remote_name: str = "origin", refspec: str | None = None, force: bool = True) -> FetchResult:
        raise OperatorIsLocal()

    def get_pull_request(self, pr_number: int) -> PullRequest | None:
        """Get a GitHub Pull Request object for the given PR number.

        Args:
            pr_number (int): The PR number to fetch

        Returns:
            PullRequest | None: The PyGitHub PullRequest object if found, None otherwise

        Note:
            This requires a GitHub API key to be set when creating the LocalRepoOperator
        """
        try:
            # Create GitHub client and get the PR
            repo = self.remote_git_repo
            if repo is None:
                logger.warning("GitHub API key is required to fetch pull requests")
                return None
            return repo.get_pull_safe(pr_number)
        except Exception as e:
            logger.warning(f"Failed to get PR {pr_number}: {e!s}")
            return None
