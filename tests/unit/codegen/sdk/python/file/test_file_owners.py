from unittest.mock import MagicMock, patch

from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_file_owners_non_codeowners_parser_returns_empty_set(tmpdir) -> None:
    # language=python
    content = """
print("hello world")
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")
        owners = file.owners
        assert len(owners) == 0


def test_file_owners_codeowners_parser_returns_non_empty_set(tmpdir) -> None:
    # language=python
    content = """
print("hello world")
"""
    mock_codeowners = MagicMock()
    mock_codeowners.of = lambda file_path: [("TEAM", "@team-owner"), ("USER", "@user-owner")] if file_path == "file.py" else {}
    with patch("codegen.git.repo_operator.repo_operator.RepoOperator.codeowners_parser", mock_codeowners):
        with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
            file = codebase.get_file("file.py")
            owners = file.owners
            assert len(owners) == 2
            assert owners == {"@team-owner", "@user-owner"}
