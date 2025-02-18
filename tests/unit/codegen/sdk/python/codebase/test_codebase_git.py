import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.mark.parametrize("commit, sync", [(True, True), (True, False), (False, False)])
def test_codebase_git(tmpdir, commit: bool, sync: bool) -> None:
    # language=python
    file0_content = """""".strip()
    other = "Other"
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"dir/file0.py": file0_content},
        programming_language=ProgrammingLanguage.PYTHON,
        commit=commit,
        sync_graph=sync,
    ) as codebase:
        default_branch = codebase.default_branch
        c1 = codebase.ctx.synced_commit
        codebase.checkout(branch=other, create_if_missing=True)
        codebase.get_file("dir/file0.py").insert_after("a = 1")
    c2 = codebase.git_commit("boop")
    commit = codebase.op.head_commit
    codebase.sync_to_commit(commit)
    assert c1 != c2
    assert codebase.get_symbol("a", optional=True) is not None
    codebase.checkout(branch=default_branch)
    assert codebase.get_symbol("a", optional=True) is None
    codebase.checkout(branch=other)
    assert codebase.get_symbol("a", optional=True) is not None


@pytest.mark.parametrize("commit, sync", [(True, True), (True, False), (False, False)])
def test_codebase_clean_repo_deletes_branches(tmpdir, commit: bool, sync: bool) -> None:
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file.py": "a = 1"}, programming_language=ProgrammingLanguage.PYTHON, commit=commit, sync_graph=sync) as codebase:
        num_branches = len(codebase._op.git_cli.branches)
        codebase.checkout(branch="foo", create_if_missing=True)
        codebase.checkout(branch="bar", create_if_missing=True)
        assert len(codebase._op.git_cli.branches) == num_branches + 2
        codebase.clean_repo()
        assert len(codebase._op.git_cli.branches) == 1
