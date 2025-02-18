import datetime as dt
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime

import psutil
from fastapi import FastAPI

from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.enums.warmup_state import WarmupState
from codegen.runner.models.apis import (
    BRANCH_ENDPOINT,
    DIFF_ENDPOINT,
    SIGNAL_SHUTDOWN_ENDPOINT,
    CreateBranchRequest,
    CreateBranchResponse,
    GetDiffRequest,
    GetDiffResponse,
    ServerInfo,
    SignalShutdownResponse,
    UtilizationMetrics,
)
from codegen.runner.sandbox.middlewares import CodemodRunMiddleware
from codegen.runner.sandbox.runner import SandboxRunner
from codegen.shared.configs.session_configs import config
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.performance.memory_utils import get_memory_stats

logger = logging.getLogger(__name__)

server_info: ServerInfo
runner: SandboxRunner


@asynccontextmanager
async def lifespan(server: FastAPI):
    global server_info
    global runner

    try:
        server_info = ServerInfo(repo_name=config.repository.full_name)
        logger.info(f"Starting up sandbox fastapi server for repo_name={server_info.repo_name}")
        repo_config = RepoConfig(
            name=config.repository.repo_name,
            full_name=config.repository.full_name,
            base_dir=os.path.dirname(config.repository.repo_path),
            language=ProgrammingLanguage(config.repository.language.upper()),
        )
        runner = SandboxRunner(repo_config=repo_config, access_token=config.secrets.github_token)
        server_info.warmup_state = WarmupState.PENDING
        await runner.warmup()
        server_info.warmup_state = WarmupState.COMPLETED
    except Exception:
        logger.exception("Failed to build graph during warmup")
        server_info.warmup_state = WarmupState.FAILED
        raise

    logger.info("Sandbox fastapi server is ready to accept requests")
    yield
    logger.info("Shutting down sandbox fastapi server")


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CodemodRunMiddleware[GetDiffRequest, GetDiffResponse],
    path=DIFF_ENDPOINT,
    server_info_fn=lambda: server_info,
    runner_fn=lambda: runner,
)
app.add_middleware(
    CodemodRunMiddleware[CreateBranchRequest, CreateBranchResponse],
    path=BRANCH_ENDPOINT,
    server_info_fn=lambda: server_info,
    runner_fn=lambda: runner,
)


@app.get("/")
def health() -> ServerInfo:
    return server_info


@app.get("/metrics/utilization", response_model=UtilizationMetrics)
async def utilization_metrics() -> UtilizationMetrics:
    # Get the current process
    process = psutil.Process(os.getpid())
    memory_stats = get_memory_stats()

    return UtilizationMetrics(
        timestamp=datetime.now(dt.UTC).isoformat(),
        memory_rss_gb=memory_stats.memory_rss_gb,
        memory_vms_gb=memory_stats.memory_vms_gb,
        cpu_percent=process.cpu_percent(),
        threads_count=process.num_threads(),
        open_files_count=len(process.open_files()),
    )


@app.post(SIGNAL_SHUTDOWN_ENDPOINT)
async def signal_shutdown() -> SignalShutdownResponse:
    logger.info(f"repo_name={server_info.repo_name} received signal_shutdown")
    server_info.is_shutting_down = True
    return SignalShutdownResponse(is_ready_to_shutdown=not server_info.is_running_codemod)


@app.post(DIFF_ENDPOINT)
async def get_diff(request: GetDiffRequest) -> GetDiffResponse:
    return await runner.get_diff(request=request)


@app.post(BRANCH_ENDPOINT)
async def create_branch(request: CreateBranchRequest) -> CreateBranchResponse:
    return await runner.create_branch(request=request)
