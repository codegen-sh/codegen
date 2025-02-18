import logging
import os
from functools import cached_property
from typing import override

from codeowners import CodeOwners as CodeOwnersParser
from git import GitCommandError

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import CheckoutResult, FetchResult, SetupOption
from codegen.git.schemas.repo_config import RepoConfig
from codegen.git.utils.clone import clone_or_pull_repo, clone_repo, pull_repo
from codegen.git.utils.clone_url import get_authenticated_clone_url_for_repo_config, get_clone_url_for_repo_config, url_to_github
from codegen.git.utils.codeowner_utils import create_codeowners_parser_for_repo
from codegen.git.utils.remote_progress import CustomRemoteProgress
from codegen.shared.performance.stopwatch_utils import stopwatch

logger = logging.getLogger(__name__)


class RemoteRepoOperator(RepoOperator):
    """A wrapper around GitPython to make it easier to interact with a cloned lowside repo."""

    # TODO: allow setting the access scope level of the lowside repo (currently it's always WRITE)
    def __init__(
        self,
        repo_config: RepoConfig,
        setup_option: SetupOption = SetupOption.PULL_OR_CLONE,
        shallow: bool = True,
        bot_commit: bool = True,
        access_token: str | None = None,
    ) -> None:
        super().__init__(repo_config=repo_config, access_token=access_token, bot_commit=bot_commit)
        self.setup_repo_dir(setup_option=setup_option, shallow=shallow)

    ####################################################################################################################
    # PROPERTIES
    ####################################################################################################################

    @property
    def clone_url(self) -> str:
        if self.access_token:
            return get_authenticated_clone_url_for_repo_config(repo=self.repo_config, token=self.access_token)
        return super().clone_url

    @property
    def default_branch(self) -> str:
        if self._default_branch is None:
            self._default_branch = self.remote_git_repo.default_branch
        return self._default_branch

    @property
    def codeowners_parser(self) -> CodeOwnersParser | None:
        if not self._codeowners_parser:
            self._codeowners_parser = create_codeowners_parser_for_repo(self.remote_git_repo)
        return self._codeowners_parser

    ####################################################################################################################
    # SET UP
    ####################################################################################################################

    @override
    def clean_repo(self) -> None:
        """Cleans the repo by:
        1. Discards any changes (tracked/untracked)
        2. Checks out the default branch (+ makes sure it's up to date with the remote)
        3. Deletes all branches except the default branch
        4. Deletes all remotes except origin

        Used in SetupOption.PULL_OR_CLONE to allow people to re-use existing repos and start from a clean state.
        """
        logger.info(f"Cleaning repo at {self.repo_path} ...")
        self.discard_changes()
        self.checkout_branch(self.default_branch, remote=True)
        self.clean_branches()
        self.clean_remotes()

    @override
    def pull_repo(self) -> None:
        """Pull the latest commit down to an existing local repo"""
        pull_repo(repo_path=self.repo_path, clone_url=self.clone_url)

    def clone_repo(self, shallow: bool = True) -> None:
        clone_repo(repo_path=self.repo_path, clone_url=self.clone_url, shallow=shallow)

    def clone_or_pull_repo(self, shallow: bool = True) -> None:
        """If repo exists, pulls changes. otherwise, clones the repo."""
        # TODO(CG-7804): if repo is not valid we should delete it and re-clone. maybe we can create a pull_repo util + use the existing clone_repo util
        if self.repo_exists():
            self.clean_repo()
        clone_or_pull_repo(repo_path=self.repo_path, clone_url=self.clone_url, shallow=shallow)

    def setup_repo_dir(self, setup_option: SetupOption = SetupOption.PULL_OR_CLONE, shallow: bool = True) -> None:
        os.makedirs(self.base_dir, exist_ok=True)
        os.chdir(self.base_dir)
        if setup_option is SetupOption.CLONE:
            # if repo exists delete, then clone, else clone
            clone_repo(shallow=shallow, repo_path=self.repo_path, clone_url=self.clone_url)
        elif setup_option is SetupOption.PULL_OR_CLONE:
            # if repo exists, pull changes, else clone
            self.clone_or_pull_repo(shallow=shallow)
        elif setup_option is SetupOption.SKIP:
            if not self.repo_exists():
                logger.warning(f"Valid git repo does not exist at {self.repo_path}. Cannot skip setup with SetupOption.SKIP.")
        os.chdir(self.repo_path)

    ####################################################################################################################
    # CHECKOUT, BRANCHES & COMMITS
    ####################################################################################################################

    def fetch_remote(self, remote_name: str = "origin", refspec: str | None = None, force: bool = True) -> FetchResult:
        """Fetches and updates a ref from a remote repository.

        Args:
            remote_name (str): Name of the remote to fetch from. Defaults to "origin".
            refspec (str | None): The refspec to fetch. If None, fetches all refs. Defaults to None.
            force (bool): If True, forces the fetch operation. Defaults to True.

        Returns:
            FetchResult: An enum indicating the result of the fetch operation.
                - SUCCESS: Fetch was successful.
                - REFSPEC_NOT_FOUND: The specified refspec doesn't exist in the remote.

        Raises:
            GitCommandError: If the fetch operation fails for reasons other than a missing refspec.

        Note:
            This force fetches by default b/c by default we prefer the remote branch over our local branch.
        """
        logger.info(f"Fetching {remote_name} with refspec {refspec}")
        progress = CustomRemoteProgress()

        try:
            self.git_cli.remotes[remote_name].fetch(refspec=refspec, force=force, progress=progress, no_tags=True)
            return FetchResult.SUCCESS
        except GitCommandError as e:
            if progress.fetch_result == FetchResult.REFSPEC_NOT_FOUND:
                return FetchResult.REFSPEC_NOT_FOUND
            else:
                raise e

    @stopwatch
    def checkout_remote_branch(self, branch_name: str | None = None, remote_name: str = "origin") -> CheckoutResult:
        """Checks out a branch from a Remote + tracks the Remote.
        If the branch_name is already checked out, does nothing
        """
        return self.checkout_branch(branch_name, remote_name=remote_name, remote=True, create_if_missing=False)

    @cached_property
    def base_url(self) -> str | None:
        repo_config = self.repo_config
        clone_url = get_clone_url_for_repo_config(repo_config)
        branch = self.get_active_branch_or_commit()
        return url_to_github(clone_url, branch)
