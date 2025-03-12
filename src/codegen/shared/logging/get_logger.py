import logging

import colorlog


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    # Force configure the root logger with a NullHandler to prevent duplicate logs
    logging.basicConfig(handlers=[logging.NullHandler()], force=True)

    formatter = colorlog.ColoredFormatter(
        "%(white)s%(asctime)s - %(name)s - %(log_color)s%(levelname)s%(reset)s%(white)s - %(message_log_color)s%(message)s",
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
        secondary_log_colors={
            "message": {
                "DEBUG": "cyan",
                "INFO": "blue",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            }
        },
    )
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        for h in logger.handlers:
            logger.removeHandler(h)

    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    # Ensure the logger propagates to the root logger
    logger.propagate = True
    # Set the level on the logger itself
    logger.setLevel(level)
    return logger
