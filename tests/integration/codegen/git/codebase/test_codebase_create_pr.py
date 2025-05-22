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


def test_codebase_create_pr_existing_pr(codebase: Codebase):
    # Create a branch and PR
    head = f"test-create-pr-existing-{uuid.uuid4()}"
    codebase.checkout(branch=head, create_if_missing=True)
    file = codebase.files[0]
    file.remove()
    codebase.commit()

    # Create the first PR
    pr1 = codebase.create_pr(title="first PR title", body="first PR body")
    assert pr1.title == "first PR title"
    assert pr1.state == "open"

    # Make another change and try to create another PR on the same branch
    file = codebase.files[1] if len(codebase.files) > 1 else codebase.create_file("new_test_file.txt", "test content")
    file.remove()
    codebase.commit()

    # This should return the existing PR instead of creating a new one
    pr2 = codebase.create_pr(title="second PR title", body="second PR body")

    # Verify it's the same PR
    assert pr2.number == pr1.number
    # The title should still be the original one since we're getting the existing PR
    assert pr2.title == "first PR title"
