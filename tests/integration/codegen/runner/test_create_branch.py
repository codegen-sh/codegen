import uuid
from http import HTTPStatus

import pytest

from codegen.git.clients.git_repo_client import GitRepoClient
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.runner.clients.codebase_client import CodebaseClient
from codegen.runner.models.apis import BRANCH_ENDPOINT, CreateBranchRequest, CreateBranchResponse
from codegen.runner.models.codemod import BranchConfig, Codemod, GroupingConfig


@pytest.mark.asyncio
@pytest.mark.timeout(60)
async def test_create_branch(codebase_client: CodebaseClient, git_repo_client: GitRepoClient, op: RepoOperator):
    # set-up
    codemod_source = """
for file in codebase.files:
    new_content = "🌈" + "\\n" + file.content
    file.edit(new_content)
    break
"""
    test_branch_name = f"codegen-test-create-branch-{uuid.uuid1()}"
    request = CreateBranchRequest(
        codemod=Codemod(user_code=codemod_source),
        commit_msg="Create branch test",
        grouping_config=GroupingConfig(),
        branch_config=BranchConfig(branch_name=test_branch_name),
    )

    # execute
    response = codebase_client.post(endpoint=BRANCH_ENDPOINT, data=request.model_dump())
    assert response.status_code == HTTPStatus.OK

    # verify
    result = CreateBranchResponse.model_validate(response.json())
    assert len(result.results) == 1
    assert result.results[0].is_complete
    assert result.results[0].error is None
    assert result.results[0].logs == ""
    assert result.results[0].observation is not None

    # verify changed files
    patch = result.results[0].observation
    lines = patch.split("\n")
    added_lines = [line[1:] for line in lines if line.startswith("+") and len(line) > 1]
    assert "🌈" in added_lines

    # verify returned branch
    assert len(result.branches) == 1
    branch = result.branches[0]
    assert branch.base_branch == "main"
    assert branch.head_ref == test_branch_name

    # verify remote branch
    remote_branch = git_repo_client.repo.get_branch(test_branch_name)
    assert remote_branch is not None
    assert remote_branch.name == test_branch_name
    assert remote_branch.commit.commit.message == "[Codegen] Create branch test"

    # clean-up
    remote = op.git_cli.remote(name="origin")
    remote.push([f":refs/heads/{test_branch_name}"])  # The colon prefix means delete
