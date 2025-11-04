import os
from typing import Optional, override

from sqlalchemy.orm import Session

from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import SetupOption
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class RemoteRepoOperator(RepoOperator):
    """A remote implementation of RepoOperator that works with repositories hosted on GitHub.

    This class extends the base RepoOperator to provide functionality specific to
    working with repositories that are hosted on GitHub or GitHub Enterprise.
    """

    db: Session
    repo_model: any  # RepoModel

    def __init__(
        self,
        db: Session,
        repo_model,
        base_dir: str = "/tmp",
        setup_option: SetupOption = SetupOption.PULL_OR_CLONE,
        shallow: bool = True,
        access_token: Optional[str] = None,
    ):
        """Initialize a RemoteRepoOperator.

        Args:
            db (Session): Database session
            repo_model: Repository model from the database
            base_dir (str): Base directory for the repository
            setup_option (SetupOption): How to set up the repository
            shallow (bool): Whether to do a shallow clone
            access_token (str): GitHub access token
        """
        self.db = db
        self.repo_model = repo_model
        repo_config = repo_model.repo_config
        repo_config.base_dir = base_dir
        super().__init__(repo_config=repo_config, setup_option=setup_option, shallow=shallow, access_token=access_token)

    @property
    @override
    def remote_git_repo(self) -> GitRepoClient:
        """Get the remote Git repository client.

        Returns:
            GitRepoClient: The remote Git repository client
        """
        if not self._remote_git_repo:
            self._remote_git_repo = GitRepoClient(self.repo_config, access_token=self.access_token)
        return self._remote_git_repo

    @override
    def setup_repo_dir(self, setup_option: SetupOption = SetupOption.PULL_OR_CLONE, shallow: bool = True) -> None:
        """Set up the repository directory.

        Args:
            setup_option (SetupOption): How to set up the repository
            shallow (bool): Whether to do a shallow clone
        """
        os.makedirs(self.base_dir, exist_ok=True)
        os.chdir(self.base_dir)
        if setup_option is SetupOption.CLONE:
            # if repo exists delete, then clone, else clone
            self.clone_repo(shallow=shallow)
        elif setup_option is SetupOption.PULL_OR_CLONE:
            # if repo exists, pull changes, else clone
            self.clone_or_pull_repo(shallow=shallow)
        elif setup_option is SetupOption.SKIP:
            if not self.repo_exists():
                logger.warning(f"Valid git repo does not exist at {self.repo_path}. Cannot skip setup with SetupOption.SKIP.")
        os.chdir(self.repo_path)
