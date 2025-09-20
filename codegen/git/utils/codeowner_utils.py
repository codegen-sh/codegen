from codeowners import CodeOwners
from github.PullRequest import PullRequest

from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.configs.constants import CODEOWNERS_FILEPATHS
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def get_filepath_owners(codeowners: CodeOwners, filepath: str) -> set[str]:
    filename_owners = codeowners.of(filepath)
    return {owner[1] for owner in filename_owners}


def is_path_owned_by_codeowner(codeowners: CodeOwners, path: str, codeowner: str) -> bool:
    filename_owners = codeowners.of(path)
    for owner in filename_owners:
        if owner[1] == codeowner:
            return True
    return False


def create_codeowners_parser_for_repo(py_github_repo: GitRepoClient) -> CodeOwners | None:
    for codeowners_filepath in CODEOWNERS_FILEPATHS:
        try:
            codeowner_file_contents = py_github_repo.get_contents(codeowners_filepath)
            if codeowner_file_contents:
                codeowners = CodeOwners(codeowner_file_contents)
                return codeowners
        except Exception as e:
            continue
    logger.info(f"Failed to create CODEOWNERS parser for repo: {py_github_repo.repo_config.name}. Returning None.")
    return None


def get_codeowners_for_pull(repo: GitRepoClient, pull: PullRequest) -> list[str]:
    codeowners_parser = create_codeowners_parser_for_repo(repo)
    if not codeowners_parser:
        logger.warning(f"Failed to create codeowners parser for repo: {repo.repo_config.name}. Returning empty list.")
        return []
    codeowners_for_pull_set = set()
    pull_files = pull.get_files()
    for file in pull_files:
        codeowners_for_file = codeowners_parser.of(file.filename)
        for codeowner_for_file in codeowners_for_file:
            codeowners_for_pull_set.add(codeowner_for_file[1])
    codeowners_for_pull_list = list(codeowners_for_pull_set)
    logger.info(f"Pull: {pull.html_url} ({pull.title}) has codeowners: {codeowners_for_pull_list}")
    return codeowners_for_pull_list
