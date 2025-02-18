from unittest.mock import patch

import pytest
from github.MainClass import Github

from codegen.git.repo_operator.remote_repo_operator import RemoteRepoOperator
from codegen.git.schemas.enums import CheckoutResult
from codegen.git.utils.file_utils import create_files

shallow_options = [True, False]


@pytest.fixture
def op(repo_config, request):
    op = RemoteRepoOperator(repo_config, shallow=request.param if hasattr(request, "param") else True, bot_commit=False)
    yield op


@pytest.mark.parametrize("op", shallow_options, ids=lambda x: f"shallow={x}", indirect=True)
@patch("codegen.git.clients.github_client.Github")
def test_checkout_branch(mock_git_client, op: RemoteRepoOperator):
    mock_git_client.return_value = Github("test_token", "https://api.github.com")
    op.pull_repo()
    op.checkout_commit(op.head_commit)
    res = op.checkout_branch("test_branch_does_not_exist", create_if_missing=False)
    assert res == CheckoutResult.NOT_FOUND
    res = op.checkout_branch("test_branch_does_not_exist", remote=True)
    assert res == CheckoutResult.NOT_FOUND
    res = op.checkout_branch("test_branch_does_not_exist", create_if_missing=True)
    assert res == CheckoutResult.SUCCESS
    res = op.checkout_branch("test_branch_does_not_exist", create_if_missing=False)
    assert res == CheckoutResult.SUCCESS
    op.clean_repo()
    res = op.checkout_branch("test_branch_does_not_exist", create_if_missing=False)
    assert res == CheckoutResult.NOT_FOUND
    op.pull_repo()
    op.checkout_commit(op.head_commit)
    op.pull_repo()


@pytest.mark.parametrize("op", [True], ids=lambda x: f"shallow={x}", indirect=True)
@patch("codegen.git.clients.github_client.Github")
def test_checkout_branch_local_already_checked_out(mock_git_client, op: RemoteRepoOperator):
    mock_git_client.return_value = Github("test_token", "https://api.github.com")

    op.checkout_commit(op.head_commit)
    op.clean_branches()
    assert len(op.git_cli.heads) == 0

    res = op.checkout_branch(op.default_branch, create_if_missing=True)
    assert res == CheckoutResult.SUCCESS
    assert op.git_cli.active_branch.name == op.default_branch
    assert len(op.git_cli.heads) == 1

    res = op.checkout_branch(op.default_branch, create_if_missing=True)  # check it out a second time should do nothing
    assert res == CheckoutResult.SUCCESS
    assert op.git_cli.active_branch.name == op.default_branch
    assert len(op.git_cli.heads) == 1


@pytest.mark.parametrize("op", [True], ids=lambda x: f"shallow={x}", indirect=True)
@patch("codegen.git.clients.github_client.Github")
def test_checkout_branch_remote_already_checked_out_resets_branch(mock_git_client, op: RemoteRepoOperator):
    mock_git_client.return_value = Github("test_token", "https://api.github.com")

    original_commit_head = op.head_commit
    assert op.git_cli.active_branch.name == op.default_branch
    # add a new commit onto the default branch
    create_files(op.repo_path, files={"test.py": "a = 1"})
    op.stage_and_commit_all_changes(message="additional commit")
    new_commit_head = op.head_commit
    assert original_commit_head.hexsha != new_commit_head.hexsha

    # checkout again onto a local branch but now with remote=True. should reset the additional commit
    res = op.checkout_branch(op.default_branch, remote=True)  # check it out a second time should do nothing
    assert res == CheckoutResult.SUCCESS
    assert len(op.git_cli.heads) == 1
    assert op.head_commit.hexsha == original_commit_head.hexsha


def test_clean_repo(op: RemoteRepoOperator):
    num_branches = len(op.git_cli.branches)
    op.checkout_branch(branch_name="test_branch", create_if_missing=True)
    with open(f"{op.repo_path}/test.txt", "w") as f:
        f.write("test")
    op.git_cli.git.add(A=True)
    op.git_cli.create_remote(name="other-remote", url=op.clone_url)

    assert op.git_cli.active_branch.name == "test_branch"
    assert len(op.git_cli.branches) == num_branches + 1
    assert len(op.git_cli.remotes) == 2
    assert op.git_cli.is_dirty()

    op.clean_repo()
    assert not op.git_cli.is_dirty()  # discards changes
    assert len(op.git_cli.branches) == 1  # deletes only the checked out branch
    assert op.git_cli.active_branch.name == op.default_branch
    assert len(op.git_cli.remotes) == 1  # deletes all remotes except origin
    assert op.git_cli.remotes[0].name == "origin"
