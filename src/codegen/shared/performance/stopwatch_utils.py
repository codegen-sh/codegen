import subprocess
import time
from functools import wraps

import sentry_sdk

from codegen.shared.logging.get_logger import get_logger
from codegen.shared.performance.time_utils import humanize_duration

logger = get_logger(__name__)


def stopwatch(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        execution_time = end_time - start_time
        logger.info(f"Function '{func.__name__}' took {humanize_duration(execution_time)} to execute.")
        return result

    return wrapper


def stopwatch_with_sentry(name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with sentry_sdk.start_transaction(name=name):
                start_time = time.perf_counter()
                res = func(*args, **kwargs)
                end_time = time.perf_counter()
                execution_time = end_time - start_time
                logger.info(f"Function '{func.__name__}' took {humanize_duration(execution_time)} to execute.")
                return res

        return wrapper

    return decorator


def subprocess_with_stopwatch(command, command_desc: str | None = None, *args, **kwargs) -> subprocess.CompletedProcess[str]:
    start_time = time.time()
    result = subprocess.run(command, *args, **kwargs)
    end_time = time.time()
    logger.info(f"Command '{command_desc or command}' took {end_time - start_time} seconds to execute.")
    return result
