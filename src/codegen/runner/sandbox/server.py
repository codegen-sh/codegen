import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from codegen.configs.models.repository import RepositoryConfig
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.enums.warmup_state import WarmupState
from codegen.runner.models.apis import (
    BRANCH_ENDPOINT,
    DIFF_ENDPOINT,
    CreateBranchRequest,
    CreateBranchResponse,
    GetDiffRequest,
    GetDiffResponse,
    ServerInfo,
)
from codegen.runner.sandbox.middlewares import CodemodRunMiddleware
from codegen.runner.sandbox.runner import SandboxRunner
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

server_info: ServerInfo
runner: SandboxRunner


@asynccontextmanager
async def lifespan(server: FastAPI):
    global server_info
    global runner

    default_repo_config = RepositoryConfig()
    repo_name = default_repo_config.full_name or default_repo_config.name
    server_info = ServerInfo(repo_name=repo_name)
    try:
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
        server_info.synced_commit = runner.op.git_cli.head.commit.hexsha
        server_info.warmup_state = WarmupState.COMPLETED
    except Exception:
        logger.exception("Failed to build graph during warmup")
        server_info.warmup_state = WarmupState.FAILED

    logger.info("Sandbox fastapi server is ready to accept requests")
    yield
    logger.info("Shutting down sandbox fastapi server")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CodemodRunMiddleware[GetDiffRequest, GetDiffResponse],
    path=DIFF_ENDPOINT,
    runner_fn=lambda: runner,
)
app.add_middleware(
    CodemodRunMiddleware[CreateBranchRequest, CreateBranchResponse],
    path=BRANCH_ENDPOINT,
    runner_fn=lambda: runner,
)


@app.get("/")
def health() -> ServerInfo:
    return server_info


@app.post(DIFF_ENDPOINT)
async def get_diff(request: GetDiffRequest) -> GetDiffResponse:
    return await runner.get_diff(request=request)


@app.post(BRANCH_ENDPOINT)
async def create_branch(request: CreateBranchRequest) -> CreateBranchResponse:
    return await runner.create_branch(request=request)
