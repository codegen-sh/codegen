import tempfile
from pathlib import Path
from typing import Generator

import pytest

from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.sdk.codebase.codebase_context import GLOBAL_FILE_IGNORE_LIST


@pytest.fixture
def tmp_dir() -> Generator[Path, None, None]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture(params=[False, True])
def mock_repo_config(request: pytest.FixtureRequest, tmp_dir: Path) -> RepoConfig:
    return RepoConfig(
        name=tmp_dir.name,
        base_dir=str(tmp_dir.parent),
        respect_gitignore=request.param,
    )


def test_get_filepaths_for_repo__empty(mock_repo_config: RepoConfig) -> None:
    repo_operator = RepoOperator(mock_repo_config)
    filepaths = repo_operator.get_filepaths_for_repo(GLOBAL_FILE_IGNORE_LIST)
    assert filepaths == []


def test_get_filepaths_for_repo__ignored_files(tmp_dir: Path, mock_repo_config: RepoConfig) -> None:
    for path in [
        "extra_ignored_dir/something.py",
        "extra_ignored_dir/oh_no_a_dependency.py",
    ]:
        file_path = tmp_dir / path
        (file_path).parent.mkdir(exist_ok=True, parents=True)
        file_path.touch()
    
    repo_operator = RepoOperator(mock_repo_config)
    filepaths = repo_operator.get_filepaths_for_repo(
        GLOBAL_FILE_IGNORE_LIST
        + [
            "extra_ignored_dir/*",
            "*/extra_ignored_dir/*",
        ],
    )
    assert filepaths == []


def test_get_filepaths_for_repo__good_files(tmp_dir: Path, mock_repo_config: RepoConfig) -> None:
    for path in [
        "src/main.py",
        "src/something_else.py",
    ]:
        file_path = tmp_dir / path
        (file_path).parent.mkdir(exist_ok=True, parents=True)
        file_path.touch()

    repo_operator = RepoOperator(mock_repo_config)
    filepaths = repo_operator.get_filepaths_for_repo(GLOBAL_FILE_IGNORE_LIST)
    assert sorted(filepaths) == sorted([
        "src/main.py",
        "src/something_else.py",
    ])

