import tempfile
from contextlib import asynccontextmanager

from fastapi import FastAPI

from codegen.runner.enums.warmup_state import WarmupState
from codegen.runner.models.apis import (
    RUN_ON_STRING_ENDPOINT,
    GetRunOnStringRequest,
    GetRunOnStringResult,
    ServerInfo,
)
from codegen.runner.sandbox.executor import SandboxExecutor
from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.compilation.string_to_code import create_execute_function_from_codeblock
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)

server_info: ServerInfo


@asynccontextmanager
async def lifespan(server: FastAPI):
    global server_info
    server_info = ServerInfo(warmup_state=WarmupState.COMPLETED)
    logger.info("Ephemeral server is ready to accept requests")
    yield
    logger.info("Shutting down fastapi server")


app = FastAPI(lifespan=lifespan)


@app.get("/")
def health() -> ServerInfo:
    return server_info


@app.post(RUN_ON_STRING_ENDPOINT)
async def run_on_string(request: GetRunOnStringRequest) -> GetRunOnStringResult:
    logger.info(f"====[ run_on_string ]====\n> Codemod source: {request.codemod_source}\n> Input: {request.files}\n> Language: {request.language}\n")
    language = ProgrammingLanguage(request.language.upper())
    with get_codebase_session(tmpdir=tempfile.mkdtemp(), files=request.files, programming_language=language) as codebase:
        executor = SandboxExecutor(codebase)
        code_to_exec = create_execute_function_from_codeblock(codeblock=request.codemod_source)
        result = await executor.execute(code_to_exec)
        logger.info(f"Result: {result}")
        return GetRunOnStringResult(result=result)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
