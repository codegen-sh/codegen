import uuid
from http import HTTPStatus

import pytest

from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.runner.clients.codebase_client import CodebaseClient
from codegen.runner.models.apis import BRANCH_ENDPOINT, CreateBranchRequest, CreateBranchResponse
from codegen.runner.models.codemod import BranchConfig, Codemod, GroupingConfig
from codegen.sdk.codebase.flagging.groupers.enums import GroupBy


@pytest.mark.timeout(120)
@pytest.mark.parametrize("group_by", [GroupBy.INSTANCE, GroupBy.FILE])
def test_create_branch_with_grouping(codebase_client: CodebaseClient, git_repo_client: GitRepoClient, op: RepoOperator, group_by: GroupBy):
    codemod_source = """
for file in codebase.files[:5]:
    flag = codebase.flag_instance(file)
    if codebase.should_fix(flag):
        new_content = "🌈" + "\\n" + file.content
        file.edit(new_content)
"""
    commit_msg = "Create branch with grouping test"
    test_branch_name = f"codegen-{uuid.uuid1()}"
    request = CreateBranchRequest(
        codemod=Codemod(user_code=codemod_source),
        commit_msg=commit_msg,
        grouping_config=GroupingConfig(group_by=group_by),
        branch_config=BranchConfig(branch_name=test_branch_name),
    )

    # execute
    response = codebase_client.post(endpoint=BRANCH_ENDPOINT, data=request.model_dump())
    assert response.status_code == HTTPStatus.OK

    # verify
    result = CreateBranchResponse.model_validate(response.json())
    assert len(result.results) == 5
    assert len(result.branches) == 5

    for i, branch in enumerate(result.branches):
        actual_branch_suffix = "-".join(branch.head_ref.split("-")[-2:])
        expected_branch_suffix = f"group-{i}"
        assert expected_branch_suffix == actual_branch_suffix

        remote_branch = git_repo_client.repo.get_branch(branch.head_ref)
        assert remote_branch is not None
        assert remote_branch.name == branch.head_ref
        assert remote_branch.commit.commit.message == f"[Codegen] {commit_msg}"
        assert remote_branch.commit.commit.author.name == "codegen-bot"

        comparison = git_repo_client.repo.compare(base=branch.base_branch, head=branch.head_ref)
        assert "+🌈" in comparison.files[0].patch

        # clean-up
        remote = op.git_cli.remote(name="origin")
        remote.push([f":refs/heads/{branch.head_ref}"])
