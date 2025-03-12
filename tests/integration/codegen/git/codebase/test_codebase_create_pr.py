import uuid

import pytest

from codegen.sdk.core.codebase import Codebase


def test_codebase_create_pr_active_branch(codebase: Codebase):
    head = f"test-create-pr-{uuid.uuid4()}"
    codebase.checkout(branch=head, create_if_missing=True)
    file = codebase.files[0]
    file.remove()
    codebase.commit()
    pr = codebase.create_pr(title="test-create-pr title", body="test-create-pr body")
    assert pr.title == "test-create-pr title"
    assert pr.body == "test-create-pr body"
    assert pr.draft is True
    assert pr.state == "open"
    assert pr.head.ref == head
    assert pr.base.ref == "main"
    assert pr.get_files().totalCount == 1
    assert pr.get_files()[0].filename == file.file_path


def test_codebase_create_pr_detached_head(codebase: Codebase):
    codebase.checkout(commit=codebase._op.git_cli.head.commit)  # move to detached head state
    with pytest.raises(ValueError) as exc_info:
        codebase.create_pr(title="test-create-pr title", body="test-create-pr body")
    assert "Cannot make a PR from a detached HEAD" in str(exc_info.value)


def test_codebase_create_pr_active_branch_is_default_branch(codebase: Codebase):
    codebase.checkout(branch=codebase._op.default_branch)
    codebase.files[0].remove()
    codebase.commit()
    with pytest.raises(ValueError) as exc_info:
        codebase.create_pr(title="test-create-pr title", body="test-create-pr body")
    assert "Cannot make a PR from the default branch" in str(exc_info.value)
