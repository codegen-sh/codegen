import logging
import traceback
from http import HTTPStatus  # Add this import
from typing import Callable, TypeVar

from starlette.background import BackgroundTasks
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from codegen.runner.sandbox.runner import SandboxRunner
from codegen.shared.exceptions.compilation import UserCodeException
from codegen.shared.performance.stopwatch_utils import stopwatch

logger = logging.getLogger(__name__)

TRequest = TypeVar("TRequest", bound=Request)
TResponse = TypeVar("TResponse", bound=Response)


class CodemodRunMiddleware[TRequest, TResponse](BaseHTTPMiddleware):
    def __init__(self, app, path: str, runner_fn: Callable[[], SandboxRunner]) -> None:
        super().__init__(app)
        self.path = path
        self.runner_fn = runner_fn

    @property
    def runner(self) -> SandboxRunner:
        return self.runner_fn()

    async def dispatch(self, request: TRequest, call_next: RequestResponseEndpoint) -> TResponse:
        if request.url.path == self.path:
            return await self.process_request(request, call_next)
        return await call_next(request)

    async def process_request(self, request: TRequest, call_next: RequestResponseEndpoint) -> TResponse:
        background_tasks = BackgroundTasks()
        try:
            logger.info(f"> (CodemodRunMiddleware) Request: {request.url.path}")
            self.runner.codebase.viz.clear_graphviz_data()
            response = await call_next(request)
            background_tasks.add_task(self.cleanup_after_codemod, is_exception=False)
            response.background = background_tasks
            return response

        except UserCodeException as e:
            message = f"Invalid user code for {request.url.path}"
            logger.info(message)
            return JSONResponse(status_code=HTTPStatus.BAD_REQUEST, content={"detail": message, "error": str(e), "traceback": traceback.format_exc()})

        except Exception as e:
            message = f"Unexpected error for {request.url.path}"
            logger.exception(message)
            res = JSONResponse(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, content={"detail": message, "error": str(e), "traceback": traceback.format_exc()})
            background_tasks.add_task(self.cleanup_after_codemod, is_exception=True)
            res.background = background_tasks
            return res

    async def cleanup_after_codemod(self, is_exception: bool = False):
        if is_exception:
            # TODO: instead of committing transactions, we should just rollback
            logger.info("Committing pending transactions due to exception")
            self.runner.codebase.ctx.commit_transactions(sync_graph=False)
        await self.reset_runner()

    @stopwatch
    async def reset_runner(self):
        logger.info("=====[ reset_runner ]=====")
        logger.info(f"Syncing runner to commit: {self.runner.commit} ...")
        self.runner.codebase.checkout(commit=self.runner.commit)
        self.runner.codebase.clean_repo()
        self.runner.codebase.checkout(branch=self.runner.codebase.default_branch, create_if_missing=True)
