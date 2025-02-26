import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from codegen.configs.models.repository import RepositoryConfig
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
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Configure logging at module level
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    force=True,
)
logger = logging.getLogger(__name__)

server_info: ServerInfo
runner: SandboxRunner


@asynccontextmanager
async def lifespan(server: FastAPI):
    global server_info
    global runner

    try:
        default_repo_config = RepositoryConfig()
        repo_name = default_repo_config.full_name or default_repo_config.name
        server_info = ServerInfo(repo_name=repo_name)
        logger.info(f"Starting up sandbox fastapi server for repo_name={repo_name}")
        repo_config = RepoConfig(
            name=default_repo_config.name,
            full_name=default_repo_config.full_name,
            base_dir=os.path.dirname(default_repo_config.path),
            language=ProgrammingLanguage(default_repo_config.language.upper()),
        )
        runner = SandboxRunner(repo_config=repo_config)
        server_info.warmup_state = WarmupState.PENDING
        await runner.warmup()
        server_info.synced_commit = runner.commit.hexsha
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
    # TODO: Sync graph to whatever changes are in the repo currently

    # Run the request
    diff_req = GetDiffRequest(codemod=Codemod(user_code=request.codemod_source))
    diff_response = await runner.get_diff(request=diff_req)
    if request.commit:
        commit_sha = runner.codebase.git_commit(f"[Codegen] {request.function_name}")
        logger.info(f"Committed changes to {commit_sha.hexsha}")
    return diff_response.result
