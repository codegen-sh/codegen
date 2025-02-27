import os
import threading
import time
from abc import ABC, abstractmethod

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class ExternalProcess(ABC):
    """Base class for all additional extrnal services that require a separate process.

    Examples include language engines, dependency managers, etc.

    Attributes:
        repo_path (str): Path to the repository root directory
        base_path (str | None): Optional subdirectory path within the repo to analyze
        full_path (str): Complete path combining repo_path and base_path
        is_ready (bool): Whether the engine has completed initialization and is ready
        error (BaseException | None): Whether the engine encountered an error during startup
    """

    repo_path: str
    base_path: str | None
    full_path: str
    is_ready: bool
    _error: BaseException | None

    def __init__(self, repo_path: str, base_path: str | None = None):
        self.repo_path: str = repo_path
        self.base_path: str | None = base_path
        self.full_path = os.path.join(repo_path, base_path) if base_path else repo_path
        self.is_ready: bool = False
        self._error: BaseException | None = None

    def start(self, async_start: bool = False):
        if async_start:
            # Create a new thread to start the engine
            thread = threading.Thread(target=self._start)
            thread.start()
        else:
            self._start()

    @abstractmethod
    def _start(self):
        pass

    def reparse(self, async_start: bool = False):
        # Reparse logic is handled by re-running start()
        self.is_ready = False
        self.start(async_start=async_start)

    def ready(self) -> bool:
        return self.is_ready

    def error(self) -> BaseException | None:
        return self._error

    def wait_until_ready(self, ignore_error: bool = False):
        logger.info(f"Waiting for {self.__class__.__name__} to be ready...")
        # Wait for 3 minutes first
        start_time = time.time()
        while not self.ready() and not self.error() and (time.time() - start_time) < 60 * 3:
            time.sleep(1)

        # After 3 minutes, check every 15 seconds and warn
        while not self.ready() and not self.error() and (time.time() - start_time) < 60 * 5:
            logger.warning(f"{self.__class__.__name__} still not ready after 3 minutes for {self.full_path}")
            time.sleep(15)

        # After 5 minutes, check every 30 seconds and error
        while not self.ready() and not self.error():
            logger.error(f"{self.__class__.__name__} still not ready after 5 minutes for {self.full_path}")
            time.sleep(30)

        if not ignore_error and self.error():
            raise self.error()
