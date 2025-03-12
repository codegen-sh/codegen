import subprocess
from dataclasses import dataclass
from pathlib import Path

import pytest
from click.testing import CliRunner

from codegen.cli.commands.reset.main import reset_command


@dataclass
class ResetTestCase:
    """Test case for reset command"""

    name: str
    changes: dict[str, str | None]
    stage: bool
    expected_content: dict[str, str | None]
    expected_staged: set[str]
    expected_modified: set[str]
    expected_untracked: set[str]
    rename_pairs: list[tuple[str, str]]


@pytest.fixture
def committed_state() -> dict[str, str]:
    """Base state that will be committed"""
    return {
        "README.md": "Base README",
        "src/hello.py": "def hello():\n    print('Original hello')",
        ".codegen/codemods/base.py": """
def base():
    pass

class MyClass:
    pass
""",
    }


@pytest.fixture
def committed_repo(initialized_repo: Path, committed_state: dict[str, str]) -> Path:
    """Repo with committed_state committed"""
    setup_repo_state(initialized_repo, committed_state)
    subprocess.run(["git", "add", "."], cwd=initialized_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=initialized_repo, check=True)
    return initialized_repo


def setup_repo_state(repo_path: Path, state: dict[str, str]):
    """Helper to set up files in the repo"""
    for filepath, content in state.items():
        file_path = repo_path / filepath
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if content is None:
            file_path.unlink()
        else:
            file_path.write_text(content)


def get_git_status(repo_path: Path) -> tuple[set[str], set[str], set[str]]:
    """Returns sets of (staged_files, modified_files, untracked_files)"""
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=repo_path,
        check=True,
        capture_output=True,
        text=True,
    )

    staged_files = set()
    modified_files = set()
    untracked_files = set()

    for line in result.stdout.splitlines():
        if not line:
            continue
        status = line[:2]
        file_path = line[3:]

        # Staged changes
        if status[0] in {"M", "A", "D", "R"}:
            staged_files.add(file_path)
        # Unstaged changes
        if status[1] in {"M", "D"}:
            modified_files.add(file_path)
        # Untracked files
        if status == "??":
            untracked_files.add(file_path)

    return staged_files, modified_files, untracked_files


def verify_git_state(
    repo_path: Path, expected_staged: set[str] | None = None, expected_modified: set[str] | None = None, expected_untracked: set[str] | None = None, rename_pairs: list[tuple[str, str]] | None = None
):
    """Verify git status matches expected state"""
    if rename_pairs is not None:
        for old_path, new_path in rename_pairs:
            corrected = f"{old_path} -> {new_path}"
            if expected_staged is not None and old_path in expected_staged:
                assert new_path in expected_staged, f"Expected {old_path} to be renamed to {new_path}, but it was not staged"
                expected_staged.remove(old_path)
                expected_staged.remove(new_path)
                expected_staged.add(corrected)

    staged, modified, untracked = get_git_status(repo_path)

    if expected_staged is not None:
        assert staged == expected_staged, f"Staged files mismatch.\nExpected: {expected_staged}\nActual: {staged}"
    if expected_modified is not None:
        assert modified == expected_modified, f"Modified files mismatch.\nExpected: {expected_modified}\nActual: {modified}"
    if expected_untracked is not None:
        assert untracked == expected_untracked, f"Untracked files mismatch.\nExpected: {expected_untracked}\nActual: {untracked}"


def verify_repo_state(repo_path: Path, expected_content: dict[str, str | None]):
    """Verify file contents in repo"""
    for path, content in expected_content.items():
        file_path = repo_path / path
        if content is None:
            assert not file_path.exists(), f"File {path} should not exist"
        else:
            assert file_path.read_text() == content, f"File {path} has wrong content"


def create_test_case(
    name: str,
    changes: dict[str, str | None],
    stage: bool,
    committed_state: dict[str, str],
    expected_content: dict[str, str | None] | None = None,
    expected_staged: set[str] | None = None,
    expected_modified: set[str] | None = None,
    expected_untracked: set[str] | None = None,
    rename_pairs: list[tuple[str, str]] = [],
) -> ResetTestCase:
    """Helper to create test cases with defaults"""
    if expected_content is None:
        expected_content = {}
        for path, content in changes.items():
            if path.startswith(".codegen"):
                expected_content[path] = content
            else:
                expected_content[path] = committed_state.get(path)

    return ResetTestCase(
        name=name,
        changes=changes,
        stage=stage,
        expected_content=expected_content,
        expected_staged=expected_staged or set(),
        expected_modified=expected_modified or set(),
        expected_untracked=expected_untracked or set(),
        rename_pairs=rename_pairs,
    )


@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            lambda committed_state: create_test_case(
                name="unstaged modifications",
                changes={
                    "README.md": "Modified README",
                    "src/hello.py": "def hello():\n    print('Modified hello')",
                    ".codegen/codemods/base.py": "def base():\n    print('Modified base')",
                },
                stage=False,
                committed_state=committed_state,
                expected_modified={".codegen/codemods/base.py"},
            ),
            id="unstaged_modifications",
        ),
        pytest.param(
            lambda committed_state: create_test_case(
                name="unstaged new files",
                changes={
                    "new.py": "print('new')",
                    ".codegen/codemods/new.py": "print('new in codegen')",
                },
                stage=False,
                committed_state=committed_state,
                expected_content={
                    "new.py": None,
                    ".codegen/codemods/new.py": "print('new in codegen')",
                },
                expected_untracked={".codegen/codemods/new.py"},
            ),
            id="unstaged_new_files",
        ),
        pytest.param(
            lambda committed_state: create_test_case(
                name="staged changes",
                changes={
                    "README.md": "Staged README",
                    "src/hello.py": "def hello():\n    print('Staged hello')",
                    ".codegen/codemods/base.py": "def base():\n    print('Staged base')",
                    "new_staged.py": "print('new staged')",
                    ".codegen/codemods/new_staged.py": "print('new staged in codegen')",
                },
                stage=True,
                committed_state=committed_state,
                expected_staged={".codegen/codemods/base.py", ".codegen/codemods/new_staged.py"},
            ),
            id="staged_changes",
        ),
        pytest.param(
            lambda committed_state: create_test_case(
                name="staged deletions",
                changes={
                    "README.md": None,
                    "src/hello.py": None,
                    ".codegen/codemods/base.py": None,
                },
                stage=True,
                committed_state=committed_state,
                expected_staged={".codegen/codemods/base.py"},
            ),
            id="staged_deletions",
        ),
        pytest.param(
            lambda committed_state: create_test_case(
                name="staged renames",
                changes={
                    ".codegen/codemods/base.py": None,  # Delete original
                    ".codegen/codemods/renamed_base.py": committed_state[".codegen/codemods/base.py"],  # Add with same content
                },
                stage=True,
                committed_state=committed_state,
                expected_staged={".codegen/codemods/base.py", ".codegen/codemods/renamed_base.py"},
                rename_pairs=[(".codegen/codemods/base.py", ".codegen/codemods/renamed_base.py")],
            ),
            id="staged_renames",
        ),
        pytest.param(
            lambda committed_state: create_test_case(
                name="unstaged renames",
                changes={
                    ".codegen/codemods/base.py": None,  # Delete original
                    ".codegen/codemods/renamed_base.py": committed_state[".codegen/codemods/base.py"],  # Add with same content
                },
                stage=False,
                committed_state=committed_state,
                expected_modified={".codegen/codemods/base.py"},
                expected_untracked={".codegen/codemods/renamed_base.py"},
                rename_pairs=[(".codegen/codemods/base.py", ".codegen/codemods/renamed_base.py")],
            ),
            id="unstaged_renames",
        ),
        pytest.param(
            lambda committed_state: create_test_case(
                name="staged rename with modifications",
                changes={
                    ".codegen/codemods/base.py": None,  # Delete original
                    ".codegen/codemods/renamed_base.py": committed_state[".codegen/codemods/base.py"] + "\n# Modified",  # Add with modified content
                },
                stage=True,
                committed_state=committed_state,
                expected_staged={".codegen/codemods/base.py", ".codegen/codemods/renamed_base.py"},
                rename_pairs=[(".codegen/codemods/base.py", ".codegen/codemods/renamed_base.py")],
            ),
            id="staged_rename_with_modifications",
        ),
    ],
)
def test_reset(committed_repo: Path, committed_state: dict[str, str], test_case: ResetTestCase, runner: CliRunner):
    """Test reset command with various scenarios"""
    # Get test case from factory function if needed
    if callable(test_case):
        test_case = test_case(committed_state)

    # Set up test state
    if test_case.changes:
        changes = {k: v for k, v in test_case.changes.items() if v is not None}
        if changes:
            setup_repo_state(committed_repo, changes)

        # Handle deletions
        for path, content in test_case.changes.items():
            if content is None:
                (committed_repo / path).unlink()
        if test_case.stage:
            subprocess.run(["git", "add", "-A"], cwd=committed_repo, check=True)

    # Run reset
    result = runner.invoke(reset_command, catch_exceptions=False)
    print(result.output)

    # Verify state
    verify_repo_state(committed_repo, test_case.expected_content)
    verify_git_state(
        committed_repo,
        expected_staged=test_case.expected_staged,
        expected_modified=test_case.expected_modified,
        expected_untracked=test_case.expected_untracked,
        rename_pairs=test_case.rename_pairs,
    )


def test_reset_with_mixed_states(committed_repo: Path, committed_state: dict[str, str], runner: CliRunner):
    """Test reset with a mix of staged, unstaged, and untracked changes"""
    # 1. Staged modifications
    staged_changes = {
        "README.md": "Staged README",
        ".codegen/codemods/base.py": "def base():\n    print('Staged base')",
    }
    setup_repo_state(committed_repo, staged_changes)
    subprocess.run(["git", "add", "."], cwd=committed_repo, check=True)

    # 2. Unstaged modifications
    unstaged_changes = {
        "README.md": "Unstaged README",
        "src/hello.py": "def hello():\n    print('Unstaged hello')",
        ".codegen/codemods/base.py": "def base():\n    print('Unstaged base')",
    }
    setup_repo_state(committed_repo, unstaged_changes)

    # 3. Untracked files
    untracked_changes = {
        "untracked.py": "print('untracked')",
        ".codegen/codemods/untracked.py": "print('untracked in codegen')",
    }
    setup_repo_state(committed_repo, untracked_changes)

    # Run reset
    runner.invoke(reset_command)

    # Verify state
    verify_repo_state(
        committed_repo,
        {
            "README.md": committed_state["README.md"],
            "src/hello.py": committed_state["src/hello.py"],
            "untracked.py": None,
            ".codegen/codemods/base.py": unstaged_changes[".codegen/codemods/base.py"],
            ".codegen/codemods/untracked.py": untracked_changes[".codegen/codemods/untracked.py"],
        },
    )

    # Verify git state
    verify_git_state(
        committed_repo,
        expected_staged={".codegen/codemods/base.py"},
        expected_modified=set(),
        expected_untracked={".codegen/codemods/untracked.py"},
    )


def test_reset_with_mixed_renames(committed_repo: Path, committed_state: dict[str, str], runner: CliRunner):
    """Test reset with a mix of staged and unstaged renames"""
    # 1. Staged rename
    staged_changes = {
        ".codegen/codemods/base.py": None,
        ".codegen/codemods/staged_rename.py": committed_state[".codegen/codemods/base.py"],
    }
    setup_repo_state(committed_repo, staged_changes)
    subprocess.run(["git", "add", "."], cwd=committed_repo, check=True)

    # 2. Unstaged rename
    unstaged_changes = {
        "README.md": None,
        "README.mdx": committed_state["README.md"],
    }
    setup_repo_state(committed_repo, unstaged_changes)
    # Don't stage these changes

    # Run reset
    runner.invoke(reset_command)

    # Verify state
    verify_repo_state(
        committed_repo,
        {
            ".codegen/codemods/base.py": None,
            ".codegen/codemods/staged_rename.py": committed_state[".codegen/codemods/base.py"],
            "README.md": committed_state["README.md"],
            "README.mdx": None,
        },
    )

    # Verify git state
    verify_git_state(
        committed_repo,
        expected_staged={".codegen/codemods/base.py", ".codegen/codemods/staged_rename.py"},
        expected_modified=set(),
        expected_untracked=set(),
        rename_pairs=[(".codegen/codemods/base.py", ".codegen/codemods/staged_rename.py")],
    )
