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

# Global OpenTelemetry handler (lazy-loaded)
_otel_handler = None
_otel_handler_checked = False

# Global telemetry config cache
_telemetry_config = None
_telemetry_config_checked = False


def _get_telemetry_config():
    """Get telemetry configuration for debug mode checking."""
    global _telemetry_config, _telemetry_config_checked

    if _telemetry_config_checked:
        return _telemetry_config

    _telemetry_config_checked = True

    try:
        # Use non-prompting config loader to avoid consent prompts during logging setup
        from codegen.configs.models.telemetry import TelemetryConfig
        from codegen.configs.constants import GLOBAL_ENV_FILE

        _telemetry_config = TelemetryConfig(env_filepath=GLOBAL_ENV_FILE)
    except ImportError:
        # Telemetry dependencies not available
        _telemetry_config = None
    except Exception:
        # Other setup errors - fallback to console logging
        _telemetry_config = None

    return _telemetry_config


def _get_otel_handler():
    """Get OpenTelemetry handler if available and enabled."""
    global _otel_handler, _otel_handler_checked

    if _otel_handler_checked:
        return _otel_handler

    _otel_handler_checked = True

    try:
        from codegen.cli.telemetry.otel_setup import get_otel_logging_handler

        _otel_handler = get_otel_logging_handler()
    except ImportError:
        # OTel dependencies not available
        _otel_handler = None
    except Exception:
        # Other setup errors
        _otel_handler = None

    return _otel_handler


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    logger = _setup_logger(name, level)
    # Note: Global exception handling is managed by cli/telemetry/exception_logger.py
    return logger


def refresh_telemetry_config():
    """Refresh the cached telemetry configuration.

    This should be called when telemetry settings change to ensure
    logging behavior updates accordingly.
    """
    global _telemetry_config_checked, _telemetry_config
    _telemetry_config_checked = False
    _telemetry_config = None


def _setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    # Force configure the root logger with a NullHandler to prevent duplicate logs
    logging.basicConfig(handlers=[logging.NullHandler()], force=True)
    logger = logging.getLogger(name)
    if logger.hasHandlers():
        for h in logger.handlers:
            logger.removeHandler(h)

    # Check telemetry configuration to determine console logging behavior
    telemetry_config = _get_telemetry_config()

    # Only add console handlers if:
    # 1. Telemetry is not configured (default behavior)
    # 2. Telemetry debug mode is enabled
    # 3. Telemetry is disabled (fallback to console logging)
    should_log_to_console = (
        telemetry_config is None  # Telemetry not configured
        or telemetry_config.debug  # Debug mode enabled
        or not telemetry_config.enabled  # Telemetry disabled
    )

    if should_log_to_console:
        logger.addHandler(stdout_handler)
        logger.addHandler(stderr_handler)

    # Always add OpenTelemetry handler if telemetry is enabled (regardless of debug mode)
    otel_handler = _get_otel_handler()
    if otel_handler is not None:
        logger.addHandler(otel_handler)

    # Ensure the logger propagates to the root logger
    logger.propagate = True
    # Set the level on the logger itself
    logger.setLevel(level)
    return logger


# Note: Exception logging is handled by cli/telemetry/exception_logger.py
