from typing import TYPE_CHECKING

from github import Repository
from github.PullRequest import PullRequest
from unidiff import PatchSet

from codegen.git.models.pull_request_context import PullRequestContext
from codegen.git.repo_operator.repo_operator import RepoOperator

if TYPE_CHECKING:
    from codegen.sdk.core.codebase import Codebase, Editable, File


def get_merge_base(git_repo_client: Repository, pull: PullRequest | PullRequestContext) -> str:
    """Gets the merge base of a pull request using a remote GitHub API client.

    Args:
        git_repo_client (GitRepoClient): The GitHub repository client.
        pull (PullRequest): The pull request object.

    Returns:
        str: The SHA of the merge base commit.
    """
    comparison = git_repo_client.compare(pull.base.sha, pull.head.sha)
    return comparison.merge_base_commit.sha


def get_file_to_changed_ranges(pull_patch_set: PatchSet) -> dict[str, list]:
    file_to_changed_ranges = {}
    for patched_file in pull_patch_set:
        # TODO: skip is deleted
        if patched_file.is_removed_file:
            continue
        changed_ranges = []  # list of changed lines for the file
        for hunk in patched_file:
            changed_ranges.append(range(hunk.target_start, hunk.target_start + hunk.target_length))
        file_to_changed_ranges[patched_file.path] = changed_ranges
    return file_to_changed_ranges


def to_1_indexed(zero_indexed_range: range) -> range:
    """Converts a n-indexed range to n+1-indexed.
    Primarily to convert 0-indexed ranges to 1 indexed
    """
    return range(zero_indexed_range.start + 1, zero_indexed_range.stop + 1)


def overlaps(range1: range, range2: range) -> bool:
    """Returns True if the two ranges overlap, False otherwise."""
    return max(range1.start, range2.start) < min(range1.stop, range2.stop)


def get_file_to_commit_sha(op: RepoOperator, pull: PullRequest) -> dict[str, str]:
    """Gets a mapping of file paths to their latest commit SHA in the PR.

    Args:
        op (RepoOperator): The repository operator
        pull (PullRequest): The pull request object

    Returns:
        dict[str, str]: A dictionary mapping file paths to their latest commit SHA
    """
    if not op.remote_git_repo:
        msg = "GitHub API client is required to get PR commit information"
        raise ValueError(msg)

    file_to_commit = {}

    # Get all commits in the PR
    commits = list(pull.get_commits())

    # Get all modified files
    files = pull.get_files()

    # For each file, find its latest commit
    for file in files:
        # Look through commits in reverse order to find the latest one that modified this file
        for commit in reversed(commits):
            # Get the files modified in this commit
            files_in_commit = commit.files
            if any(f.filename == file.filename for f in files_in_commit):
                file_to_commit[file.filename] = commit.sha
                break

        # If we didn't find a commit (shouldn't happen), use the head SHA
        if file.filename not in file_to_commit:
            file_to_commit[file.filename] = pull.head.sha

    return file_to_commit


class CodegenPR:
    """Wrapper around PRs - enables codemods to interact with them"""

    _gh_pr: PullRequest
    _codebase: "Codebase"
    _op: RepoOperator

    # =====[ Computed ]=====
    _modified_file_ranges: dict[str, list[tuple[int, int]]] = None

    def __init__(self, op: RepoOperator, codebase: "Codebase", pr: PullRequest):
        self._op = op
        self._gh_pr = pr
        self._codebase = codebase

    @property
    def modified_file_ranges(self) -> dict[str, list[tuple[int, int]]]:
        """Files and the ranges within that are modified"""
        if not self._modified_file_ranges:
            pull_patch_set = self.get_pull_patch_set()
            self._modified_file_ranges = get_file_to_changed_ranges(pull_patch_set)
        return self._modified_file_ranges

    @property
    def modified_files(self) -> list["File"]:
        filenames = self.modified_file_ranges.keys()
        return [self._codebase.get_file(f, optional=True) for f in filenames]

    def is_modified(self, editable: "Editable") -> bool:
        """Returns True if the Editable's range contains any modified lines"""
        filepath = editable.filepath
        changed_ranges = self._modified_file_ranges.get(filepath, [])
        symbol_range = to_1_indexed(editable.line_range)
        if any(overlaps(symbol_range, changed_range) for changed_range in changed_ranges):
            return True
        return False

    @property
    def modified_symbols(self) -> list[str]:
        # Import SourceFile locally to avoid circular dependencies
        from codegen.sdk.core.file import SourceFile

        all_modified = []
        for file in self.modified_files:
            if file is None:
                print("Warning: File is None")
                continue
            if not isinstance(file, SourceFile):
                continue
            for symbol in file.symbols:
                if self.is_modified(symbol):
                    all_modified.append(symbol.name)

        return all_modified

    def get_pr_diff(self) -> str:
        """Get the full diff of the PR"""
        if not self._op.remote_git_repo:
            msg = "GitHub API client is required to get PR diffs"
            raise ValueError(msg)

        # Get the diff directly from the PR
        status, _, res = self._op.remote_git_repo.repo._requester.requestJson("GET", self._gh_pr.url, headers={"Accept": "application/vnd.github.v3.diff"})
        if status != 200:
            msg = f"Failed to get PR diff: {res}"
            raise Exception(msg)
        return res

    def get_pull_patch_set(self) -> PatchSet:
        diff = self.get_pr_diff()
        pull_patch_set = PatchSet(diff)
        return pull_patch_set

    def get_commit_sha(self) -> str:
        """Get the commit SHA of the PR"""
        return self._gh_pr.head.sha

    def get_file_commit_shas(self) -> dict[str, str]:
        """Get a mapping of file paths to their latest commit SHA in the PR"""
        return get_file_to_commit_sha(op=self._op, pull=self._gh_pr)
