import logging
import shutil
from collections.abc import Generator
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import filelock
import pytest
from _pytest.python import Metafunc
from pyinstrument import Profiler

from codegen.git.repo_operator.local_repo_operator import LocalRepoOperator
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.codebase.config import CodebaseConfig, ProjectConfig
from codegen.sdk.core.codebase import Codebase
from codegen.shared.configs.models.feature_flags import CodebaseFeatureFlags
from tests.shared.codemod.constants import DIFF_FILEPATH
from tests.shared.codemod.models import BASE_PATH, BASE_TMP_DIR, VERIFIED_CODEMOD_DIFFS, CodemodMetadata, Repo, Size
from tests.shared.codemod.test_discovery import find_codemod_test_cases, find_repos, find_verified_codemod_cases
from tests.shared.utils.recursion import set_recursion_limit

if TYPE_CHECKING:
    from codemods.codemod import Codemod

logger = logging.getLogger(__name__)

ONLY_STORE_CHANGED_DIFFS = True


def pytest_generate_tests(metafunc: Metafunc) -> None:
    if metafunc.definition.name == "test_verified_codemods":
        cases = []
        for case in find_verified_codemod_cases(metafunc):
            cases.append(case)

        metafunc.parametrize(
            "codemod_metadata,repo,expected",
            [
                pytest.param(
                    i.codemod_metadata,
                    i.repo,
                    i.test_dir,
                    marks=[pytest.mark.xdist_group(i.repo.name), pytest.mark.skipif(i.should_skip, reason="file marked as skip")],
                )
                for i in cases
            ],
            indirect=["repo", "expected"],
            ids=[f"{i.codemod_metadata.name}-{i.repo.name}" for i in cases],
            scope="session",
        )
        return

    extra_repo_flag = metafunc.config.getoption("--extra-repos")
    if isinstance(extra_repo_flag, str):
        extra_repo_flag = extra_repo_flag.lower() == "true"
    repos = find_repos(extra_repo_flag)
    size = list(map(Size, metafunc.config.getoption("--size")))

    match metafunc.definition.name:
        case "test_codemods_cloned_repos":
            cases = []
            for case in find_codemod_test_cases(repos):
                if case.repo.size not in size:
                    continue
                cases.append(case)

            metafunc.parametrize(
                "raw_codemod,repo,expected",
                [
                    pytest.param(
                        i.codemod_metadata.codemod,
                        i.repo,
                        i.test_dir,
                        marks=[pytest.mark.xdist_group(i.repo.name), pytest.mark.skipif(i.should_skip, reason="file marked as skip")],
                    )
                    for i in cases
                ],
                indirect=["repo", "expected"],
                ids=[f"{i.codemod_metadata.name}-{i.repo.name}" for i in cases],
                scope="session",
            )
        case "test_codemods_parse":
            to_test = {name: repo for name, repo in repos.items()}
            metafunc.parametrize(
                "repo",
                [pytest.param(repo, marks=pytest.mark.xdist_group(repo.name)) for repo in to_test.values()],
                indirect=["repo"],
                ids=to_test.keys(),
                scope="session",
            )


@pytest.fixture(autouse=True)
def auto_profile(request):
    if not request.config.getoption("--profile"):
        yield
        return
    PROFILE_ROOT = BASE_PATH / ".profiles"
    # Turn profiling on
    profiler = Profiler()
    profiler.start()
    try:
        yield  # Run test
    finally:
        profiler.stop()
        PROFILE_ROOT.mkdir(exist_ok=True)
        results_file = PROFILE_ROOT / f"{request.node.name}.html"
        profiler.write_html(results_file)


DIFF_ROOT = BASE_PATH / ".diffs"

type YieldFixture[T] = Generator[T, None, None]


@pytest.fixture(scope="session")
def db():
    yield MagicMock()


@pytest.fixture(scope="session")
def repo(request) -> Generator[Repo, None, None]:
    yield request.param


@pytest.fixture(scope="session")
def token(request):
    yield request.config.getoption("--token")


@pytest.fixture(scope="session")
def op(repo: Repo, token: str | None) -> YieldFixture[LocalRepoOperator]:
    with filelock.FileLock(BASE_TMP_DIR / "locks" / repo.name):
        op = repo.to_op(repo.name, token)
        yield op


Codebases: dict[str, Codebase] = {}


@pytest.fixture()
def _codebase(repo: Repo, op: RepoOperator, request) -> YieldFixture[Codebase]:
    sync = request.config.getoption("sync-graph").lower() == "true"
    log_parse = request.config.getoption("log-parse").lower() == "true"
    feature_flags = CodebaseFeatureFlags(verify_graph=sync, debug=log_parse)
    if repo.name not in Codebases:
        projects = [ProjectConfig(repo_operator=op, programming_language=repo.language, subdirectories=repo.subdirectories, base_path=repo.base_path)]
        Codebases[repo.name] = Codebase(projects=projects, config=CodebaseConfig(feature_flags=feature_flags))
    codebase = Codebases[repo.name]
    codebase.reset(git_reset=True)
    yield codebase
    codebase.reset(git_reset=True)


@pytest.fixture
def input_dir(request):
    yield request.param


@pytest.fixture
def expected(op: RepoOperator, request) -> Path | str:
    """Get the expected git diff or directory"""
    test_dir: Path = request.param
    diff_file = test_dir / DIFF_FILEPATH
    expected_dir = test_dir / "expected"
    if diff_file.exists() or VERIFIED_CODEMOD_DIFFS in test_dir.parents:
        if expected_dir.exists():
            shutil.rmtree(expected_dir)
        return diff_file
    return expected_dir


@pytest.fixture
def codebase(_codebase: Codebase) -> YieldFixture[Codebase]:
    """Ensures codebase is reset for every test"""
    set_recursion_limit()
    with _codebase.session(commit=False, sync_graph=False):
        yield _codebase


@pytest.fixture
def diff_folder(request):
    diff_path = DIFF_ROOT / request.node.name
    diff_path.mkdir(exist_ok=True, parents=True)
    yield diff_path


@pytest.fixture
def codemod(raw_codemod: type["Codemod"]):
    codemod = raw_codemod()
    return codemod


@pytest.fixture
def verified_codemod(codemod_metadata: CodemodMetadata, expected: Path) -> YieldFixture["Codemod"]:
    # write the diff to the file
    diff_path = expected
    diff_path.parent.mkdir(parents=True, exist_ok=True)
    if not diff_path.exists() or not diff_path.read_text():
        logger.info(f"Writing diff to {diff_path}")
        diff = codemod_metadata.diff
        if diff:
            with diff_path.open("w") as f:
                f.write(diff)
        else:
            logger.warning(f"No diff found for codemod: {codemod_metadata.codemod_id}")
    codemod = codemod_metadata.codemod
    # Ensure the execute method is added to the codemod
    assert hasattr(codemod, "execute"), "codemod has no execute method"
    yield codemod
    if ONLY_STORE_CHANGED_DIFFS and diff_path.exists() and diff_path.read_text().strip() == codemod_metadata.diff.strip():
        logger.info(f"Removing diff {diff_path}")
        diff_path.unlink()
