import sys

from codegen.configs.models.codebase import CodebaseConfig
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import SetupOption
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.models.apis import CreateBranchRequest, CreateBranchResponse, GetDiffRequest, GetDiffResponse
from codegen.runner.sandbox.executor import SandboxExecutor
from codegen.sdk.codebase.config import ProjectConfig, SessionOptions
from codegen.sdk.codebase.factory.codebase_factory import CodebaseType
from codegen.sdk.core.codebase import Codebase
from codegen.shared.compilation.string_to_code import create_execute_function_from_codeblock
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class SandboxRunner:
    """Responsible for orchestrating the lifecycle of a warmed sandbox"""

    # =====[ __init__ instance attributes ]=====
    repo: RepoConfig
    op: RepoOperator | None

    # =====[ computed instance attributes ]=====
    codebase: CodebaseType
    executor: SandboxExecutor

    def __init__(self, repo_config: RepoConfig, op: RepoOperator | None = None) -> None:
        self.repo = repo_config
        self.op = op or RepoOperator(repo_config=self.repo, setup_option=SetupOption.PULL_OR_CLONE, bot_commit=True)

    async def warmup(self, codebase_config: CodebaseConfig | None = None) -> None:
        """Warms up this runner by cloning the repo and parsing the graph."""
        logger.info(f"===== Warming runner for {self.repo.full_name or self.repo.name} =====")
        sys.setrecursionlimit(10000)  # for graph parsing

        self.codebase = await self._build_graph(codebase_config)
        self.executor = SandboxExecutor(self.codebase)

    async def _build_graph(self, codebase_config: CodebaseConfig | None = None) -> Codebase:
        logger.info("> Building graph...")
        projects = [ProjectConfig(programming_language=self.repo.language, repo_operator=self.op, base_path=self.repo.base_path, subdirectories=self.repo.subdirectories)]
        return Codebase(projects=projects, config=codebase_config)

    async def get_diff(self, request: GetDiffRequest) -> GetDiffResponse:
        custom_scope = {"context": request.codemod.codemod_context} if request.codemod.codemod_context else {}
        code_to_exec = create_execute_function_from_codeblock(codeblock=request.codemod.user_code, custom_scope=custom_scope)
        session_options = SessionOptions(max_transactions=request.max_transactions, max_seconds=request.max_seconds)

        res = await self.executor.execute(code_to_exec, session_options=session_options)

        return GetDiffResponse(result=res)

    async def create_branch(self, request: CreateBranchRequest) -> CreateBranchResponse:
        custom_scope = {"context": request.codemod.codemod_context} if request.codemod.codemod_context else {}
        code_to_exec = create_execute_function_from_codeblock(codeblock=request.codemod.user_code, custom_scope=custom_scope)
        branch_config = request.branch_config

        branch_config.custom_base_branch = branch_config.custom_base_branch or self.codebase.default_branch
        self.executor.remote_repo.set_up_base_branch(branch_config.custom_base_branch)
        self.executor.remote_repo.set_up_head_branch(branch_config.custom_head_branch, branch_config.force_push_head_branch)

        response = CreateBranchResponse()
        if "codebase.flag_instance" in request.codemod.user_code:
            flags = await self.executor.find_flags(code_to_exec)
            flag_groups = await self.executor.find_flag_groups(flags, request.grouping_config)
            response.num_flags = len(flags)
            response.group_segments = [group.segment for group in flag_groups]
            if len(flag_groups) == 0:
                logger.info("No flag groups found. Running without flagging.")
                flag_groups = [None]
        else:
            flag_groups = [None]

        # TODO: do this as part of find_flag_groups?
        max_prs = request.grouping_config.max_prs
        if max_prs and len(flag_groups) >= max_prs:
            logger.info(f"Max PRs limit reached: {max_prs}. Skipping remaining groups.")
            flag_groups = flag_groups[:max_prs]

        run_results, branches = await self.executor.execute_flag_groups(request.commit_msg, code_to_exec, flag_groups, branch_config)
        response.results = run_results
        response.branches = branches

        self.codebase.ctx.flags._flags.clear()
        return response
