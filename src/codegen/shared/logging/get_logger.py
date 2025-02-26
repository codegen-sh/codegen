import logging

import colorlog


def get_colored_logger(name: str) -> logging.Logger:
    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
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
    )

    logger = logging.getLogger(name)
    logger.addHandler(handler)
    return logger
