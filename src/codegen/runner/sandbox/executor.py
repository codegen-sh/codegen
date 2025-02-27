from collections.abc import Callable
from datetime import UTC, datetime

from github.PullRequest import PullRequest

from codegen.git.models.pr_options import PROptions
from codegen.runner.diff.get_raw_diff import get_raw_diff
from codegen.runner.models.codemod import BranchConfig, CodemodRunResult, CreatedBranch, GroupingConfig
from codegen.runner.sandbox.repo import SandboxRepo
from codegen.runner.utils.branch_name import get_head_branch_name
from codegen.runner.utils.exception_utils import update_observation_meta
from codegen.sdk.codebase.config import SessionOptions
from codegen.sdk.codebase.factory.codebase_factory import CodebaseType
from codegen.sdk.codebase.flagging.code_flag import CodeFlag
from codegen.sdk.codebase.flagging.group import Group
from codegen.sdk.codebase.flagging.groupers.utils import get_grouper_by_group_by
from codegen.shared.exceptions.control_flow import StopCodemodException
from codegen.shared.logging.get_logger import get_logger
from codegen.shared.performance.stopwatch_utils import stopwatch
from codegen.visualizations.viz_utils import get_graph_json

logger = get_logger(__name__)


class SandboxExecutor:
    """Responsible for executing the user defined codemod in the sandbox."""

    codebase: CodebaseType
    remote_repo: SandboxRepo

    def __init__(self, codebase: CodebaseType):
        self.codebase = codebase
        self.remote_repo = SandboxRepo(self.codebase)

    async def find_flags(self, execute_func: Callable) -> list[CodeFlag]:
        """Runs the execute_func in find_mode to find flags"""
        self.codebase.set_find_mode(True)
        await self._execute_with_try_catch(execute_func, commit=False)
        code_flags = self.codebase.ctx.flags._flags
        logger.info(f"> Found {len(self.codebase.ctx.flags._flags)} CodeFlags")
        return code_flags

    async def find_flag_groups(self, code_flags: list[CodeFlag], grouping_config: GroupingConfig) -> list[Group]:
        """Groups the code flags as specified by grouping_config"""
        if grouping_config.subdirectories and len(grouping_config.subdirectories) > 0:
            logger.info(f"> Filtering flags by subdirectories: {grouping_config.subdirectories}")
            code_flags = [flag for flag in code_flags if any([flag.filepath.startswith(x) for x in grouping_config.subdirectories])]
            logger.info(f"> Flags remaining: {len(code_flags)}")

        # =====[ Group the code flags ]=====
        logger.info(f"> Grouping CodeFlags by config: {grouping_config}")
        grouper = get_grouper_by_group_by(grouping_config.group_by)
        groups = grouper.create_all_groups(flags=code_flags, repo_operator=self.codebase.op)
        logger.info(f"> Created {len(groups)} groups")
        return groups

    async def execute_flag_groups(self, commit_msg: str, execute_func: Callable, flag_groups: list[Group], branch_config: BranchConfig) -> tuple[list[CodemodRunResult], list[CreatedBranch]]:
        run_results = []
        head_branches = []
        for idx, group in enumerate(flag_groups):
            if idx > 0 and run_results[-1].error:
                logger.info("Skipping remaining groups because of error in previous group")
                break
            if group:
                logger.info(f"Running group {group.segment} ({idx + 1} out of {len(flag_groups)})...")

            head_branch = branch_config.custom_head_branch or get_head_branch_name(branch_config.branch_name, group)
            logger.info(f"Running with head branch: {head_branch}")
            self.remote_repo.reset_branch(branch_config.custom_base_branch, head_branch)

            run_result = await self.execute(execute_func, group=group)
            created_branch = CreatedBranch(base_branch=branch_config.custom_base_branch, head_ref=None)
            if self.remote_repo.push_changes_to_remote(commit_msg, head_branch, branch_config.force_push_head_branch):
                created_branch.head_ref = head_branch

            self.codebase.reset()
            run_results.append(run_result)
            head_branches.append(created_branch)

        self.codebase.ctx.flags._flags.clear()
        return run_results, head_branches

    async def execute(self, execute_func: Callable, group: Group | None = None, session_options: SessionOptions = SessionOptions()) -> CodemodRunResult:
        """Runs the execute_func in edit_mode and returns the saved the result"""
        self.codebase.set_find_mode(False)
        if group:
            self.codebase.set_active_group(group)
        result = await self._execute_with_try_catch(execute_func, session_options=session_options)
        return await self._get_structured_run_output(result)

    async def execute_on_pr(self, execute_func: Callable, pr: PullRequest, session_options: SessionOptions = SessionOptions()) -> CodemodRunResult:
        """Runs the execute_func in edit_mode and returns the saved the result"""
        # TODO: only difference is this sets `set_find_mode` to True to capture flags. Shouldn't need to do this, flags should always appear.
        self.codebase.set_find_mode(True)
        result = await self._execute_with_try_catch(execute_func, session_options=session_options, pr=pr)
        return await self._get_structured_run_output(result)

    @stopwatch
    async def _execute_with_try_catch(
        self,
        execute_func: Callable,
        *,
        sync_graph: bool = False,
        commit: bool = True,
        session_options: SessionOptions = SessionOptions(),
        pr: PullRequest | None = None,
    ) -> CodemodRunResult:
        """Runs the execute_func in a try/catch with a codebase session"""
        logger.info(f"Running safe execute with sync_graph: {sync_graph} commit: {commit} session_options: {session_options}")
        result = CodemodRunResult()
        pr_options = PROptions()
        try:
            with self.codebase.session(sync_graph, commit, session_options=session_options):
                execute_func(self.codebase, pr_options, pr=pr)
                result.is_complete = True

        except StopCodemodException as e:
            logger.info(f"Stopping codemod due to {e.__class__.__name__}: {e}")
            result.observation_meta = update_observation_meta(e, result.observation_meta)
            result.is_complete = True

        except Exception as e:
            error_message = str(e)
            logger.exception(e)
            result.error = error_message
            result.is_complete = False

        finally:
            # =====[ Capture completed_at ]=====
            result.completed_at = datetime.now(tz=UTC)

            # =====[ Capture PR options ]=====
            result.pr_options = pr_options

            # =====[ Build graph.json ]=====
            viz_results = get_graph_json(self.codebase.op)
            if viz_results is not None:
                result.visualization = viz_results

        return result

    async def _get_structured_run_output(self, result: CodemodRunResult) -> CodemodRunResult:
        """Formats output into a CodemodRunResult"""
        # =====[ Save flags ]=====
        # Note: I think we should just store this on the CodemodRunResult.flags, not meta
        # Also note: we should type this object, since we end up using it in several locations
        flags = [
            {
                "filepath": flag.symbol.filepath,
                "startLine": flag.symbol.start_point.row,
                "startColumn": flag.symbol.start_point.column,
                "endLine": flag.symbol.end_point.row,
                "endColumn": flag.symbol.end_point.column,
                "message": flag.message,
                "messageType": str(flag.message_type),
                "messageRecipient": flag.message_recipient,
            }
            for flag in self.codebase.ctx.flags._flags
        ]
        result.flags = flags
        if result.observation_meta is None:
            result.observation_meta = {}
        result.observation_meta["flags"] = flags

        # =====[ Get and store raw diff ]=====
        logger.info("> Extracting diff")
        raw_diff = get_raw_diff(codebase=self.codebase)
        result.observation = raw_diff
        result.base_commit = self.codebase.current_commit.hexsha if self.codebase.current_commit else "HEAD"

        # =====[ Finalize CodemodRun state ]=====
        # Include logs etc.
        logger.info("> Extracting/formatting logs")
        result.logs = self.codebase.get_finalized_logs()
        return result
