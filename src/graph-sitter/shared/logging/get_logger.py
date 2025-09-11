import logging
import sys

import colorlog

formatter = colorlog.ColoredFormatter(
    "%(white)s%(asctime)s - %(name)s - %(log_color)s%(levelname)s%(reset)s%(white)s - %(message_log_color)s%(message)s",
    log_colors={
        "DEBUG": "white",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
    secondary_log_colors={
        "message": {
            "DEBUG": "cyan",
            "INFO": "white",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        }
    },
)


class StdOutFilter(logging.Filter):
    def filter(self, record):
        return record.levelno < logging.ERROR


class StdErrFilter(logging.Filter):
    def filter(self, record):
        return record.levelno >= logging.ERROR


# Create handlers
stdout_handler = logging.StreamHandler(sys.stdout)  # Logs to stdout
stdout_handler.setFormatter(formatter)
stdout_handler.addFilter(StdOutFilter())

stderr_handler = logging.StreamHandler(sys.stderr)  # Logs to stderr
stderr_handler.setFormatter(formatter)
stderr_handler.addFilter(StdErrFilter())


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = _setup_logger(name, level)
    _setup_exception_logging(logger)
    return logger


def _setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    # Force configure the root logger with a NullHandler to prevent duplicate logs
    logging.basicConfig(handlers=[logging.NullHandler()], force=True)
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        for h in logger.handlers:
            logger.removeHandler(h)

    logger.addHandler(stdout_handler)
    logger.addHandler(stderr_handler)

    # Ensure the logger propagates to the root logger
    logger.propagate = True
    # Set the level on the logger itself
    logger.setLevel(level)
    return logger


def _setup_exception_logging(logger: logging.Logger) -> None:
    def log_exception(exc_type, exc_value, exc_traceback):
        logger.exception("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    # Set the log_exception function as the exception hook
    sys.excepthook = log_exception
