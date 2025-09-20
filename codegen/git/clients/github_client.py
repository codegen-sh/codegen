from github import Consts
from github.GithubException import UnknownObjectException
from github.MainClass import Github
from github.Organization import Organization
from github.Repository import Repository

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class GithubClient:
    """Manages interaction with GitHub"""

    base_url: str
    _client: Github

    def __init__(self, token: str | None = None, base_url: str = Consts.DEFAULT_BASE_URL):
        self.base_url = base_url
        self._client = Github(token, base_url=base_url)

    @property
    def client(self) -> Github:
        return self._client

    ####################################################################################################################
    # CHECK RUNS
    ####################################################################################################################

    def get_repo_by_full_name(self, full_name: str) -> Repository | None:
        try:
            return self._client.get_repo(full_name)
        except UnknownObjectException as e:
            return None
        except Exception as e:
            logger.warning(f"Error getting repo {full_name}:\n\t{e}")
            return None

    def get_organization(self, org_name: str) -> Organization | None:
        try:
            return self._client.get_organization(org_name)
        except UnknownObjectException as e:
            return None
        except Exception as e:
            logger.warning(f"Error getting org {org_name}:\n\t{e}")
            return None
