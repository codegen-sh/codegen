from unittest.mock import PropertyMock, patch

import pytest

from codegen.runner.sandbox.runner import SandboxRunner


@pytest.mark.asyncio
@patch("codegen.runner.sandbox.executor.SandboxExecutor")
async def test_sandbox_runner_warmup_builds_graph(mock_executor, runner: SandboxRunner):
    await runner.warmup()
    assert runner.codebase.files
    assert len(runner.codebase.files) == 1


@pytest.mark.asyncio
@patch("codegen.runner.sandbox.runner.SandboxRunner._build_graph")
async def test_sandbox_runner_warmup_builds_graph_throws(mock_build_graph, runner: SandboxRunner):
    mock_build_graph.side_effect = Exception("Test exception")

    with pytest.raises(Exception):
        await runner.warmup()


@pytest.mark.asyncio
@patch("codegen.runner.sandbox.runner.logger")
@patch("codegen.runner.sandbox.runner.SandboxExecutor")
async def test_sandbox_runner_warmup_logs_repo_id(mock_executor, mock_logger, runner: SandboxRunner):
    await runner.warmup()
    assert runner.codebase.files
    assert len(runner.codebase.files) == 1
    assert mock_logger.info.call_count == 1
    assert "Warming runner for test-repo" in mock_logger.info.call_args_list[0][0][0]


@pytest.mark.asyncio
@patch("codegen.runner.sandbox.runner.SandboxExecutor")
async def test_sandbox_runner_warmup_starts_with_default_branch(mock_executor, runner: SandboxRunner):
    await runner.warmup()  # assert True is returned
    # assert len(runner.codebase._op.git_cli.branches) == 1  TODO: fix GHA creating master and main branch
    assert not runner.codebase._op.git_cli.head.is_detached
    assert runner.codebase._op.git_cli.active_branch.name == runner.codebase.default_branch
    assert runner.codebase._op.git_cli.head.commit == runner.commit


@pytest.mark.asyncio
@patch("codegen.runner.sandbox.runner.logger")
@patch("codegen.runner.sandbox.runner.SandboxExecutor")
@patch("codegen.sdk.core.codebase.Codebase.default_branch", new_callable=PropertyMock)
async def test_sandbox_runner_reset_runner_deletes_branches(mock_branch, mock_executor, mock_logger, runner: SandboxRunner):
    mock_branch.return_value = "main"
    await runner.warmup()
    num_branches = len(runner.codebase._op.git_cli.heads)  # TODO: fix GHA creating master and main branch and assert the len is 1 at the start
    runner.codebase.checkout(branch="test-branch-a", create_if_missing=True)
    runner.codebase.checkout(branch="test-branch-b", create_if_missing=True)
    assert len(runner.codebase._op.git_cli.heads) == num_branches + 2
    runner.reset_runner()
    assert len(runner.codebase._op.git_cli.heads) == 1  # now should be on default branch at self.commit
    assert runner.codebase._op.git_cli.active_branch.name == runner.codebase.default_branch
    assert runner.codebase._op.git_cli.head.commit == runner.commit


# @pytest.mark.asyncio
# @patch("codegen.runner.sandbox.executor.get_runner_feature_flags")
# @patch("codegen.runner.sandbox.executor.SandboxExecutor.execute")
# async def test_sandbox_runner_run_reset_runner_same_branch_state(
#     mock_run_execute_flag_groups,
#     mock_ffs,
#     runner: SandboxRunner,
#     db_mock: DBMock,
#     db_mock_connection: MockConnectionProvider,
# ):
#     """Test that the branch post warm-up state and the post reset_runner state is the same"""
#     mock_ffs.return_value = RunnerFeatureFlags()
#     mock_run_execute_flag_groups.return_value = CodemodRunResult()
#     session = db_mock_connection.get_session()
#     mock_source = """
# codebase.files[0].edit("a = 2")
# """
#
#     # after warmup sandbox is on default branch at self.commit
#     await runner.warmup()
#     assert not runner.codebase._op.git_cli.head.is_detached
#     assert runner.codebase._op.git_cli.active_branch.name == runner.codebase.default_branch
#     assert runner.codebase._op.git_cli.head.commit == runner.commit
#
#     mock_instances = [*create_mock_codemod_run(create_epic=True, codemod_version_source=mock_source)]
#     with db_mock.from_orm(mock_instances) as mocked_data:
#         cm_run = mocked_data[CodemodRunModel][0]
#         cm_version = mocked_data[CodemodVersionModel][0]
#         epic = mocked_data[TaskEpicModel][0]
#         codemod = serialize_mock_cm_run(cm_run, cm_version, epic)
#         branch_config = BranchConfig(base_branch=runner.codebase.default_branch)
#         request = CreateBranchRequest(codemod=codemod, grouping_config=GroupingConfig(), branch_config=branch_config)
#         await runner.create_branch(request=request)
#
#     # assert a PR branch was created
#     assert "codegen-codemod-1-version-1-run-1-group-0" in runner.codebase._op.git_cli.heads
#
#     # after running and resetting runner, sandbox is again on default branch at self.commit
#     runner.reset_runner()
#     assert len(runner.codebase._op.git_cli.heads) == 1  # now should be on default branch at self.commit
#     assert not runner.codebase._op.git_cli.head.is_detached
#     assert runner.codebase._op.git_cli.active_branch.name == runner.codebase.default_branch
#     assert runner.codebase._op.git_cli.head.commit == runner.commit
#
#
# @pytest.mark.asyncio
# @patch("codegen.runner.sandbox.runner.logger")
# async def test_run_user_code_exception_sets_failure_returns_empty_codemod_run_result(mock_logger, runner: SandboxRunner):
#     with pytest.raises(InvalidUserCodeException):
#         mock_syntax_error_source = """
#   = 1
# """
#         mock_db = MagicMock()
#         mock_db.get().repo.language = ProgrammingLanguage.PYTHON
#         mock_cm_run = MagicMock(
#             spec=CodemodRunModel, epic=MagicMock(id=1234, link="link", user=MagicMock(github_username="user"), title="test-epic"), codemod_version=MagicMock(id=123, source=mock_syntax_error_source)
#         )
#         req = GetDiffRequest(codemod=serialize_cm_run(mock_cm_run))
#
#         await runner.get_diff(request=req)
#
#         assert mock_logger.error.call_count == 1
#         assert "InvalidUserCodeException caught compiling codemod version: 123" in mock_logger.error.call_args_list[0][0][0]
#         assert "SyntaxError" in mock_cm_run.error
#         assert "invalid syntax" in mock_cm_run.error
