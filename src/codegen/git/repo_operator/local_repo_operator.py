from typing import Self

from sqlalchemy.orm import Session

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import SetupOption
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class LocalRepoOperator(RepoOperator):
    """A local implementation of RepoOperator that works with local repositories.

    This class extends the base RepoOperator to provide functionality specific to
    working with repositories that are already on the local filesystem.
    """

    @classmethod
    def from_repo_id(cls, db: Session, repo_id: int, setup_option: SetupOption = SetupOption.PULL_OR_CLONE, shallow: bool = True) -> Self:
        """Create a LocalRepoOperator from a repository ID in the database.

        Args:
            db (Session): Database session
            repo_id (int): ID of the repository in the database
            setup_option (SetupOption): How to set up the repository
            shallow (bool): Whether to do a shallow clone

        Returns:
            Self: A new LocalRepoOperator instance
        """
        from app.db import RepoModel

        repo_model = RepoModel.find_by_id(db, repo_id)
        if not repo_model:
            msg = f"Repository with ID {repo_id} not found"
            raise ValueError(msg)

        return cls(repo_model=repo_model, setup_option=setup_option, shallow=shallow)

    def __init__(
        self,
        repo_model,
        base_dir: str = "/tmp",
        setup_option: SetupOption = SetupOption.PULL_OR_CLONE,
        shallow: bool = True,
    ):
        """Initialize a LocalRepoOperator.

        Args:
            repo_model: Repository model from the database
            base_dir (str): Base directory for the repository
            setup_option (SetupOption): How to set up the repository
            shallow (bool): Whether to do a shallow clone
        """
        self.repo_model = repo_model
        repo_config = repo_model.repo_config
        repo_config.base_dir = base_dir
        super().__init__(repo_config=repo_config, setup_option=setup_option, shallow=shallow)
