import importlib
import inspect
import json
import os
import textwrap
from collections.abc import Generator, Iterator
from pathlib import Path

import emoji
from loguru import logger

from codegen.gscli.generate.runner_imports import get_runner_imports
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codemods.codemod import Codemod
from tests.shared.codemod.constants import DIFF_FILEPATH
from tests.shared.codemod.models import BASE_PATH, CODEMOD_PATH, REPO_ID_TO_URL, TEST_DIR, VERIFIED_CODEMOD_DATA_DIR, VERIFIED_CODEMOD_DIFFS, ClonedRepoTestCase, CodemodMetadata, Repo, Size
from tests.shared.codemod.verified_codemod_utils import CodemodAPI, RepoCodemodMetadata, SkillTestConfig, anonymize_id


def find_repos(
    extra_repos: bool = False,
    sizes: list[Size] | None = None,
    languages: list[ProgrammingLanguage] | None = None,
) -> dict[str, Repo]:
    sizes = sizes or [size for size in Size]
    languages = languages or [language for language in ProgrammingLanguage]
    results = {}
    repo_path = TEST_DIR / ("repos/extra" if extra_repos else "repos/open_source")
    for file in repo_path.glob("*.json"):
        text = file.read_bytes()
        repo = Repo.from_json(text)
        if repo.size not in sizes:
            continue
        if repo.language not in languages:
            continue
        results[repo.name] = repo
    return results


def find_verified_codemod_repos() -> dict[str, Repo]:
    repo_commits_file = VERIFIED_CODEMOD_DATA_DIR / "repo_commits.json"
    with repo_commits_file.open("r") as f:
        repos_to_commits = json.load(f)

    # ===== [STORE REPOS] =====
    repos: dict[str, Repo] = {}
    for repo_name, metadata in repos_to_commits.items():
        for commit_metadata in metadata:
            commit = commit_metadata["commit"]
            language = commit_metadata["language"]
            url = commit_metadata["url"]
            unique_name = f"{repo_name}_{commit}"
            repo = Repo(commit=commit, url=url, language=language, size=Size.Large, extra_repo=True, name=unique_name)
            repos[unique_name] = repo
    return repos


def codemods_from_dir(codemod_dir: Path) -> Iterator[CodemodMetadata]:
    for file in codemod_dir.glob("*.py"):
        relative = file.relative_to(BASE_PATH).with_suffix("")
        import_path = str(relative).removeprefix("src/").replace("/", ".")
        mod = importlib.import_module(import_path)
        for name, value in inspect.getmembers(mod, inspect.isclass):
            if issubclass(value, Codemod) and name != "Codemod":
                yield CodemodMetadata(codemod=value, category=codemod_dir.parent.name, directory=codemod_dir)


def find_test_cases(codemod_dir: Path, repos: dict[str, Repo], codemod: CodemodMetadata) -> Generator[ClonedRepoTestCase, None, None]:
    for dir in codemod_dir.iterdir():
        if dir.is_dir() and "__pycache__" != dir.name:
            repo_name = dir.name.removeprefix("test_")
            if repo_name in repos:
                repo = repos[repo_name]
                yield ClonedRepoTestCase(test_dir=dir, repo=repo, codemod_metadata=codemod, diff_path=dir / DIFF_FILEPATH)


def find_codemods() -> Generator[CodemodMetadata, None, None]:
    for directory in CODEMOD_PATH.iterdir():
        if directory.name == "repos" or directory.is_file():
            continue
        for codemod_dir in directory.iterdir():
            yield from codemods_from_dir(codemod_dir)


def find_codemod_test_cases(repos: dict[str, Repo]) -> Generator[ClonedRepoTestCase, None, None]:
    for codemod in find_codemods():
        test_dir = codemod.test_dir
        if not test_dir.exists() and codemod.category == "canonical":
            logger.warning(f"No tests exist for {codemod.name}")
        if test_dir.exists():
            tests = list(find_test_cases(codemod_dir=test_dir, repos=repos, codemod=codemod))
            if all(test.repo.extra_repo for test in tests):
                logger.warning(f"All tests for {codemod.name} are against extra repositories")
            elif len(tests) == 0:
                logger.warning(f"No tests exist for {codemod.name}")
            yield from tests


def filter_repos(repos: dict):
    if total_nodes := os.getenv("CIRCLE_NODE_TOTAL", None):
        total_nodes = int(total_nodes)
        index = int(os.getenv("CIRCLE_NODE_INDEX"))
        res = {k: repos[k] for idx, k in enumerate(sorted(repos.keys())) if idx % total_nodes == index}
        return res
    return repos


def find_verified_codemod_cases(metafunc):
    """Generate test cases for a list of codemods"""
    repos = {}
    config = SkillTestConfig.from_metafunc(metafunc)
    codemod_api = CodemodAPI(api_key=config.api_key)
    for repo_id, url in filter_repos(REPO_ID_TO_URL).items():
        if config.repo_id and repo_id != config.repo_id:
            continue

        codemods_data = RepoCodemodMetadata.from_json_file(VERIFIED_CODEMOD_DATA_DIR / f"{anonymize_id(repo_id)}.json")
        codemods_data.filter(base_commit=config.base_commit, codemod_id=config.codemod_id)

        repo_name = codemods_data.repo_name
        programming_language = codemods_data.language

        for commit, codemods in codemods_data.codemods_by_base_commit.items():
            repo_dir_name = f"{repo_name}_{commit}"
            if repo_dir_name not in repos:
                repo = Repo(
                    commit=commit,
                    url=url,
                    language=programming_language,
                    size=Size.Large,
                    extra_repo=True,
                    name=repo_dir_name,
                )
                repos[repo_dir_name] = repo
            yield from generate_codemod_test_cases(repos[repo_dir_name], codemods, codemod_api)


def escape_codemod_name(name: str) -> str:
    """Escape a codemod name to be filesystem and python safe.

    Removes all characters except letters, numbers, underscores, and dashes.
    """
    import re

    # First demojize any emojis
    name = emoji.demojize(name)
    # Convert to ASCII, replacing non-ASCII chars
    name = name.encode("ascii", "namereplace").decode()
    # Keep only alphanumeric chars, underscores and dashes
    name = re.sub(r"[^\w\-]", "_", name)
    return name


def generate_codemod_test_cases(repo: Repo, codemods: list[CodemodMetadata], codemod_api: CodemodAPI) -> Generator[ClonedRepoTestCase, None, None]:
    """Generate test cases for a list of codemods"""
    for codemod_data in codemods:
        test_dir = VERIFIED_CODEMOD_DIFFS / codemod_data.anonymized_name
        diff_path = test_dir / DIFF_FILEPATH
        # add the execute method to the codemod
        execute_func = create_function_from_string("execute", codemod_data)
        name = escape_codemod_name(codemod_data.name) + "-" + str(codemod_data.codemod_id)
        codemod = Codemod(name=name, execute=execute_func)

        codemod_metadata = CodemodMetadata(
            codemod=codemod,
            category="verified_codemod",
            directory=VERIFIED_CODEMOD_DIFFS,
            repo_app_id=codemod_data.repo_app_id,
            codemod_id=codemod_data.codemod_id,
            codemod_url=codemod_data.codemod_url,
            codemod_api=codemod_api,
            empty_diff=codemod_data.diff is None,
            diff=codemod_data.diff,
        )
        yield ClonedRepoTestCase(
            test_dir=test_dir,
            repo=repo,
            codemod_metadata=codemod_metadata,
            diff_path=diff_path,
        )


def create_function_from_string(function_name, codemod):
    """Adds a function to a class instance using a string of code.

    Args:
        function_name: Name of the function to create
        skill: Skill object containing the function code

    Returns:
        The function object if successful, None if there was an error
    """
    # Create a namespace for the execution
    code_string = codemod.source

    namespace = {}
    import_str = get_runner_imports(include_private_imports=False, include_codegen=False)
    # Prepare the code string by ensuring proper indentation
    code_string = code_string.strip()
    # logger.info(f"Adding function: \n{code_string}\n")
    code_string = import_str + "\n\n" + "def " + function_name + "(codebase):\n" + textwrap.indent(code_string, "    ")

    try:
        # Execute the code string in our namespace
        exec(code_string, namespace)

        # Get the function from our namespace
        function = namespace[function_name]

        return function
    except Exception as e:
        logger.error(f"Error adding function for codemod: {codemod.codemod_id}, codemod: {codemod.codemod_url}, error: {e!s}")
        raise e
