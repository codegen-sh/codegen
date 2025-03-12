import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from codegen.configs.models.codebase import DefaultCodebaseConfig
from codegen.git.configs.constants import CODEGEN_BOT_EMAIL, CODEGEN_BOT_NAME
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.enums import SetupOption
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.enums.warmup_state import WarmupState
from codegen.runner.models.apis import (
    RUN_FUNCTION_ENDPOINT,
    GetDiffRequest,
    RunFunctionRequest,
    ServerInfo,
)
from codegen.runner.models.codemod import Codemod, CodemodRunResult
from codegen.runner.sandbox.runner import SandboxRunner
from codegen.shared.logging.get_logger import get_logger

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)
logger = get_logger(__name__)

server_info: ServerInfo
runner: SandboxRunner


@asynccontextmanager
async def lifespan(server: FastAPI):
    global server_info
    global runner

    try:
        repo_config = RepoConfig.from_envs()
        server_info = ServerInfo(repo_name=repo_config.full_name or repo_config.name)

        # Set the bot email and username
        op = RepoOperator(repo_config=repo_config, setup_option=SetupOption.SKIP, bot_commit=True)
        runner = SandboxRunner(repo_config=repo_config, op=op)
        logger.info(f"Configuring git user config to {CODEGEN_BOT_EMAIL} and {CODEGEN_BOT_NAME}")
        runner.op.git_cli.git.config("user.email", CODEGEN_BOT_EMAIL)
        runner.op.git_cli.git.config("user.name", CODEGEN_BOT_NAME)

        # Parse the codebase with sync enabled
        logger.info(f"Starting up fastapi server for repo_name={repo_config.name}")
        server_info.warmup_state = WarmupState.PENDING
        codebase_config = DefaultCodebaseConfig.model_copy(update={"sync_enabled": True})
        await runner.warmup(codebase_config=codebase_config)
        server_info.synced_commit = runner.op.head_commit.hexsha
        server_info.warmup_state = WarmupState.COMPLETED

    except Exception:
        logger.exception("Failed to build graph during warmup")
        server_info.warmup_state = WarmupState.FAILED

    logger.info("Local daemon is ready to accept requests!")
    yield
    logger.info("Shutting down local daemon server")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health() -> ServerInfo:
    return server_info


@app.post(RUN_FUNCTION_ENDPOINT)
async def run(request: RunFunctionRequest) -> CodemodRunResult:
    _save_uncommitted_changes_and_sync()
    diff_req = GetDiffRequest(codemod=Codemod(user_code=request.codemod_source))
    diff_response = await runner.get_diff(request=diff_req)
    if request.commit:
        if commit_sha := runner.codebase.git_commit(f"[Codegen] {request.function_name}", exclude_paths=[".codegen/*"]):
            logger.info(f"Committed changes to {commit_sha.hexsha}")
    return diff_response.result


def _save_uncommitted_changes_and_sync() -> None:
    if commit := runner.codebase.git_commit("[Codegen] Save uncommitted changes", exclude_paths=[".codegen/*"]):
        logger.info(f"Saved uncommitted changes to {commit.hexsha}")

    cur_commit = runner.op.head_commit
    if cur_commit != runner.codebase.ctx.synced_commit:
        logger.info(f"Syncing codebase to head commit: {cur_commit.hexsha}")
        runner.codebase.sync_to_commit(target_commit=cur_commit)
    else:
        logger.info("Codebase is already synced to head commit")

    server_info.synced_commit = cur_commit.hexsha
