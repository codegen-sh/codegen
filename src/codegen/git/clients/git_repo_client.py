import time
from datetime import datetime

from github.Branch import Branch
from github.CheckRun import CheckRun
from github.CheckSuite import CheckSuite
from github.Commit import Commit
from github.GithubException import GithubException, UnknownObjectException
from github.GithubObject import NotSet, Opt
from github.Issue import Issue
from github.IssueComment import IssueComment
from github.Label import Label
from github.PullRequest import PullRequest
from github.Repository import Repository
from github.Tag import Tag
from github.Workflow import Workflow

from codegen.configs.models.secrets import SecretsConfig
from codegen.git.clients.github_client import GithubClient
from codegen.git.schemas.repo_config import RepoConfig
from codegen.git.utils.format import format_comparison
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class GitRepoClient:
    """Wrapper around PyGithub's Remote Repository."""

    repo_config: RepoConfig
    gh_client: GithubClient
    _repo: Repository

    def __init__(self, repo_config: RepoConfig, access_token: str | None = None) -> None:
        self.repo_config = repo_config
        self.gh_client = self._create_github_client(token=access_token or SecretsConfig().github_token)
        self._repo = self._create_client()

    def _create_github_client(self, token: str) -> GithubClient:
        return GithubClient(token=token)

    def _create_client(self) -> Repository:
        client = self.gh_client.get_repo_by_full_name(self.repo_config.full_name)
        if not client:
            msg = f"Repo {self.repo_config.full_name} not found!"
            raise ValueError(msg)
        return client

    @property
    def repo(self) -> Repository:
        return self._repo

    ####################################################################################################################
    # PROPERTIES
    ####################################################################################################################

    @property
    def default_branch(self) -> str:
        return self.repo.default_branch

    ####################################################################################################################
    # CONTENTS
    ####################################################################################################################

    def get_contents(self, file_path: str, ref: str | None = None) -> str | None:
        """Returns string file content on a given ref"""
        if not ref:
            ref = self.default_branch
        try:
            file = self.repo.get_contents(file_path, ref=ref)
            file_contents = file.decoded_content.decode("utf-8")  # type: ignore[union-attr]
            return file_contents
        except UnknownObjectException:
            logger.info(f"File: {file_path} not found in ref: {ref}")
            return None
        except GithubException as e:
            if e.status == 404:
                logger.info(f"File: {file_path} not found in ref: {ref}")
                return None
            raise

    def get_last_modified_date_of_path(self, path: str) -> datetime:
        """Uses the GitHub API to return the last modified date of a given directory or file.

        Args:
        ----
            path (str): The path to the directory within the repository.

        Returns:
        -------
            str: The last modified date of the directory in ISO format (YYYY-MM-DDTHH:MM:SSZ).

        """
        commits = self.repo.get_commits(path=path)
        if commits.totalCount > 0:
            # Get the date of the latest commit
            last_modified_date = commits[0].commit.committer.date
            return last_modified_date
        else:
            print("Directory has not been modified or does not exist.")
            return datetime.min

    ####################################################################################################################
    # COMMENTS
    ####################################################################################################################

    def create_review_comment(
        self,
        pull: PullRequest,
        body: str,
        commit: Commit,
        path: str,
        line: Opt[int] = NotSet,
        side: Opt[str] = NotSet,
        start_line: Opt[int] = NotSet,
    ) -> None:
        # TODO: add protections (ex: can write to PR)
        writeable_pr = self.repo.get_pull(pull.number)
        writeable_pr.create_review_comment(
            body=body,
            commit=commit,
            path=path,
            line=line,
            side=side,
            start_line=start_line,
        )

    def create_issue_comment(
        self,
        pull: PullRequest,
        body: str,
    ) -> IssueComment:
        # TODO: add protections (ex: can write to PR)
        writeable_pr = self.repo.get_pull(pull.number)
        return writeable_pr.create_issue_comment(body=body)

    ####################################################################################################################
    # PULL REQUESTS
    ####################################################################################################################

    def get_pull_by_branch_and_state(
        self,
        head_branch_name: str | None = None,
        base_branch_name: str | None = None,
        state: str = "all",
    ) -> PullRequest | None:
        """Returns the first PR for the head/base/state filter"""
        if not head_branch_name:
            logger.info("No head branch name provided. Unable to find PR.")
            return None
        if not base_branch_name:
            base_branch_name = self.default_branch

        head_branch_name = f"{self.repo_config.organization_name}:{head_branch_name}"

        # retrieve all pulls ordered by created descending
        prs = self.repo.get_pulls(base=base_branch_name, head=head_branch_name, state=state, sort="created", direction="desc")
        if prs.totalCount > 0:
            return prs[0]
        else:
            return None

    def get_pull_safe(self, number: int) -> PullRequest | None:
        """Returns a PR by its number
        TODO: catching UnknownObjectException is common enough to create a decorator
        """
        try:
            pr = self.repo.get_pull(number)
            return pr
        except UnknownObjectException as e:
            return None
        except Exception as e:
            logger.warning(f"Error getting PR by number: {number}\n\t{e}")
            return None

    def get_or_create_pull(
        self,
        head_branch_name: str,
        base_branch_name: str | None = None,  # type: ignore[assignment]
        title: str | None = None,  # type: ignore[assignment]
        body: str | None = None,  # type: ignore[assignment]
    ) -> PullRequest | None:
        pull = self.get_pull_by_branch_and_state(head_branch_name=head_branch_name, base_branch_name=base_branch_name)
        if pull:
            logger.info(f"Pull request for head branch: {head_branch_name} already exists. Skip creation.")
        else:
            logger.info(f"Creating pull request base: {base_branch_name} head: {head_branch_name} ...")
            pull = self.create_pull(head_branch_name=head_branch_name, base_branch_name=base_branch_name, title=title, body=body)
        return pull

    def create_pull(
        self,
        head_branch_name: str,
        base_branch_name: str | None = None,
        title: str | None = None,
        body: str | None = None,
        draft: bool = True,
    ) -> PullRequest | None:
        if base_branch_name is None:
            base_branch_name = self.default_branch

        # draft PRs are not supported on all private repos
        # TODO: check repo plan features instead of this heuristic
        if self.repo.visibility == "private":
            logger.info(f"Repo {self.repo.name} is private. Disabling draft PRs.")
            draft = False

        try:
            pr = self.repo.create_pull(title=title or f"Draft PR for {head_branch_name}", body=body or "", head=head_branch_name, base=base_branch_name, draft=draft)
            logger.info(f"Created pull request for head branch: {head_branch_name} at {pr.html_url}")
            # NOTE: return a read-only copy to prevent people from editing it
            return self.repo.get_pull(pr.number)
        except GithubException as ge:
            logger.warning(f"Failed to create PR got GithubException\n\t{ge}")
        except Exception as e:
            logger.warning(f"Failed to create PR:\n\t{e}")

        return None

    def squash_and_merge(self, base_branch_name: str, head_branch_name: str, squash_commit_msg: str | None = None, squash_commit_title: str | None = None) -> None:
        # =====[ Step 1: Make a squash PR ]=====
        # We will do a squash merge via a pull request, since regular
        # merges in PyGithub do not support `squash`
        squash_pr = self.create_pull(
            base_branch_name=base_branch_name,
            head_branch_name=head_branch_name,
            draft=False,
            title=squash_commit_title,
            body="",
        )
        # TODO: handle PR not mergeable due to merge conflicts
        merge = squash_pr.merge(commit_message=squash_commit_msg, commit_title=squash_commit_title, merge_method="squash")  # type: ignore[arg-type]

    def edit_pull(self, pull: PullRequest, title: Opt[str] = NotSet, body: Opt[str] = NotSet, state: Opt[str] = NotSet) -> None:
        writable_pr = self.repo.get_pull(pull.number)
        writable_pr.edit(title=title, body=body, state=state)

    def add_label_to_pull(self, pull: PullRequest, label: Label) -> None:
        writeable_pr = self.repo.get_pull(pull.number)
        writeable_pr.add_to_labels(label)

    def remove_label_from_pull(self, pull: PullRequest, label: Label) -> None:
        writeable_pr = self.repo.get_pull(pull.number)
        writeable_pr.remove_from_labels(label)

    ####################################################################################################################
    # BRANCHES
    ####################################################################################################################

    def get_or_create_branch(self, new_branch_name: str, base_branch_name: str | None = None) -> Branch | None:
        try:
            existing_branch = self.get_branch_safe(new_branch_name)
            if existing_branch:
                return existing_branch
            new_branch = self.create_branch(new_branch_name, base_branch_name=base_branch_name)
            return new_branch
        except Exception as e:
            logger.exception(f"Unexpected error creating branch: {new_branch_name}\n\t{e}")
            return None

    def get_branch_safe(self, branch_name: str, attempts: int = 1, wait_seconds: int = 1) -> Branch | None:
        for i in range(attempts):
            try:
                return self.repo.get_branch(branch_name)
            except GithubException as e:
                if e.status == 404 and i < attempts - 1:
                    time.sleep(wait_seconds)
            except Exception as e:
                logger.warning(f"Unexpected error getting branch: {branch_name}\n\t{e}")
        return None

    def create_branch(self, new_branch_name: str, base_branch_name: str | None = None) -> Branch | None:
        if base_branch_name is None:
            base_branch_name = self.default_branch

        base_branch = self.repo.get_branch(base_branch_name)
        # TODO: also wrap git ref. low pri b/c the only write operation on refs is creating one
        self.repo.create_git_ref(sha=base_branch.commit.sha, ref=f"refs/heads/{new_branch_name}")
        branch = self.get_branch_safe(new_branch_name)
        return branch

    def create_branch_from_sha(self, new_branch_name: str, base_sha: str) -> Branch | None:
        self.repo.create_git_ref(ref=f"refs/heads/{new_branch_name}", sha=base_sha)
        branch = self.get_branch_safe(new_branch_name)
        return branch

    def delete_branch(self, branch_name: str) -> None:
        if branch_name == self.default_branch:
            logger.warning("Deleting the default branch is not allowed! Skipping delete.")
            return
        # TODO: log event

        branch_to_delete = self.get_branch_safe(branch_name)
        if branch_to_delete:
            ref_to_delete = self.repo.get_git_ref(f"heads/{branch_name}")
            ref_to_delete.delete()
            logger.info(f"Branch: {branch_name} deleted successfully!")
        else:
            logger.info(f"Branch: {branch_name} does not exist. Skipping delete.")

    ####################################################################################################################
    # COMMITS
    ####################################################################################################################

    def get_commit_safe(self, commit_sha: str) -> Commit | None:
        try:
            return self.repo.get_commit(commit_sha)
        except UnknownObjectException as e:
            logger.warning(f"Commit {commit_sha} not found:\n\t{e}")
            return None
        except Exception as e:
            logger.warning(f"Error getting commit {commit_sha}:\n\t{e}")
            return None

    ####################################################################################################################
    # DIFFS
    ####################################################################################################################

    def get_commit_diff(self, commit: Commit, show_commits: bool = False) -> str:
        """Diff of a single commit"""
        return self.compare_commits(commit.parents[0], commit, show_commits=show_commits)

    def get_pr_diff(self, pr: PullRequest, show_commits: bool = False) -> str:
        return self.compare(pr.base.sha, pr.head.sha, show_commits=show_commits)

    def compare_commits(self, base_commit: Commit, head_commit: Commit, show_commits: bool = False) -> str:
        return self.compare(base_commit.sha, head_commit.sha, show_commits=show_commits)

    # TODO: make base_branch param optional
    def compare_branches(self, base_branch_name: str | None, head_branch_name: str, show_commits: bool = False) -> str:
        """Comparison between two branches"""
        if base_branch_name is None:
            base_branch_name = self.default_branch
        return self.compare(base_branch_name, head_branch_name, show_commits=show_commits)

    # NOTE: base utility that other compare functions should try to use
    def compare(self, base: str, head: str, show_commits: bool = False) -> str:
        comparison = self.repo.compare(base, head)
        return format_comparison(comparison, show_commits=show_commits)

    ####################################################################################################################
    # LABELS
    ####################################################################################################################

    # TODO: also wrap labels in safe wrapper to allow making edits
    def get_label_safe(self, label_name: str) -> Label | None:
        try:
            label_name = label_name.strip()
            label = self.repo.get_label(label_name)
            return label
        except UnknownObjectException as e:
            return None
        except Exception as e:
            logger.warning(f"Error getting label by name: {label_name}\n\t{e}")
            return None

    def create_label(self, label_name: str, color: str) -> Label:
        # TODO: also offer description field
        label_name = label_name.strip()
        self.repo.create_label(label_name, color)
        # TODO: is there a way to convert new_label to a read-only label without making another API call?
        # NOTE: return a read-only label to prevent people from editing it
        return self.repo.get_label(label_name)

    def get_or_create_label(self, label_name: str, color: str) -> Label:
        existing_label = self.get_label_safe(label_name)
        if existing_label:
            return existing_label
        return self.create_label(label_name=label_name, color=color)

    ####################################################################################################################
    # CHECK SUITES
    ####################################################################################################################

    def get_check_suite_safe(self, check_suite_id: int) -> CheckSuite | None:
        try:
            return self.repo.get_check_suite(check_suite_id)
        except UnknownObjectException as e:
            return None
        except Exception as e:
            logger.warning(f"Error getting check suite by id: {check_suite_id}\n\t{e}")
            return None

    ####################################################################################################################
    # CHECK RUNS
    ####################################################################################################################

    def get_check_run_safe(self, check_run_id: int) -> CheckRun | None:
        try:
            return self.repo.get_check_run(check_run_id)
        except UnknownObjectException as e:
            return None
        except Exception as e:
            logger.warning(f"Error getting check run by id: {check_run_id}\n\t{e}")
            return None

    def create_check_run(
        self,
        name: str,
        head_sha: str,
        details_url: Opt[str] = NotSet,
        status: Opt[str] = NotSet,
        conclusion: Opt[str] = NotSet,
        output: Opt[dict[str, str | list[dict[str, str | int]]]] = NotSet,
    ) -> CheckRun:
        new_check_run = self.repo.create_check_run(name=name, head_sha=head_sha, details_url=details_url, status=status, conclusion=conclusion, output=output)
        return self.repo.get_check_run(new_check_run.id)

    ####################################################################################################################
    # WORKFLOW
    ####################################################################################################################

    def get_workflow_safe(self, file_name: str) -> Workflow | None:
        try:
            return self.repo.get_workflow(file_name)
        except UnknownObjectException as e:
            return None
        except Exception as e:
            logger.warning(f"Error getting workflow by file name: {file_name}\n\t{e}")
            return None

    def create_workflow_dispatch(self, workflow: Workflow, ref: Branch | Tag | Commit | str, inputs: Opt[dict] = NotSet):
        writeable_workflow = self.repo.get_workflow(workflow.id)
        writeable_workflow.create_dispatch(ref=ref, inputs=inputs)

    ####################################################################################################################
    # FORKS
    ####################################################################################################################

    def merge_upstream(self, branch_name: str) -> bool:
        """:calls: `POST /repos/{owner}/{repo}/merge-upstream <http://docs.github.com/en/rest/reference/repos#sync-a-fork-branch-with-the-upstream-repository>`_
        :param branch: string
        :rtype: bool

        Copied from: https://github.com/PyGithub/PyGithub/pull/2066. Remove after this change is merged into PyGithub.
        """
        assert isinstance(branch_name, str), branch_name
        post_parameters = {"branch": branch_name}
        status, _, _ = self.repo._requester.requestJson("POST", f"{self.repo.url}/merge-upstream", input=post_parameters)
        return status == 200

    ####################################################################################################################
    # SEARCH
    ####################################################################################################################

    def search_issues(self, query: str, **kwargs) -> list[Issue]:
        return self.gh_client.client.search_issues(query, **kwargs)

    def search_prs(self, query: str, **kwargs) -> list[PullRequest]:
        return self.gh_client.client.search_issues(query, **kwargs)
