import time

from git import RemoteProgress

from codegen.git.schemas.enums import FetchResult
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class CustomRemoteProgress(RemoteProgress):
    fetch_result: FetchResult | None = None
    last_line_time: float | None = None

    def _parse_progress_line(self, line) -> None:
        self.line_dropped(line)
        if "fatal: couldn't find remote ref" in line:
            self.fetch_result = FetchResult.REFSPEC_NOT_FOUND

    def line_dropped(self, line) -> None:
        if self.last_line_time is None or time.time() - self.last_line_time > 1:
            logger.info(line)
            self.last_line_time = time.time()

    def update(
        self,
        op_code: int,
        cur_count: str | float,
        max_count: str | float | None = None,
        message: str = "",
    ) -> None:
        logger.info(f"message: {message} op_code: {op_code} cur_count: {cur_count} max_count: {max_count}")
