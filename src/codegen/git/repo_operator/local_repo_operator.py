import logging
import os

from git import Repo as GitCLI

from codegen.git.repo_operator.local_git_repo import LocalGitRepo
from codegen.git.repo_operator.repo_operator import RepoOperator
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
