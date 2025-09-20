"""Global exception logging for CLI telemetry.

This module provides a global exception handler that captures unhandled exceptions
and logs them through the existing OpenTelemetry telemetry system.
"""

import sys
import traceback
from typing import Any

from codegen.shared.logging.get_logger import get_logger
from codegen.cli.telemetry.otel_setup import get_session_uuid, get_otel_logging_handler
from codegen.cli.telemetry.consent import ensure_telemetry_consent

# Initialize logger for exception handling
logger = get_logger(__name__)

# Store the original excepthook to allow chaining
_original_excepthook = sys.excepthook


def _get_exception_context(exc_type: type[BaseException], exc_value: BaseException, tb: Any) -> dict[str, Any]:
    """Extract relevant context from an exception for logging.

    Args:
        exc_type: The exception type
        exc_value: The exception instance
        tb: The traceback object

    Returns:
        Dictionary with exception context for structured logging
    """
    context = {
        "operation": "cli.unhandled_exception",
        "exception_type": exc_type.__name__,
        "exception_message": str(exc_value),
        "session_id": get_session_uuid(),
    }

    # Add module and function information from the traceback
    if tb is not None:
        # Get the last frame (where the exception occurred)
        last_frame = tb
        while last_frame.tb_next is not None:
            last_frame = last_frame.tb_next

        frame = last_frame.tb_frame
        context.update(
            {
                "exception_file": frame.f_code.co_filename,
                "exception_function": frame.f_code.co_name,
                "exception_line": last_frame.tb_lineno,
            }
        )

        # Get the full stack trace as a string
        context["stack_trace"] = "".join(traceback.format_exception(exc_type, exc_value, tb))

        # Add command context if available from CLI args
        try:
            # Try to extract command information from sys.argv
            if len(sys.argv) > 1:
                context["cli_command"] = sys.argv[1]
                context["cli_args"] = sys.argv[2:] if len(sys.argv) > 2 else []
        except Exception:
            # Don't let context extraction break exception logging
            pass

    return context


def global_exception_handler(exc_type: type[BaseException], exc_value: BaseException, tb: Any) -> None:
    """Global exception handler that logs unhandled exceptions.

    This function is designed to be set as sys.excepthook to capture all unhandled
    exceptions in the CLI and log them through the telemetry system.

    Args:
        exc_type: The exception type
        exc_value: The exception instance
        tb: The traceback object
    """
    # Skip logging for KeyboardInterrupt (Ctrl+C) - this is expected user behavior
    if issubclass(exc_type, KeyboardInterrupt):
        # Call the original excepthook for normal handling
        _original_excepthook(exc_type, exc_value, tb)
        return

    # Skip logging for SystemExit with code 0 (normal exit)
    if issubclass(exc_type, SystemExit) and getattr(exc_value, "code", None) == 0:
        _original_excepthook(exc_type, exc_value, tb)
        return

    try:
        # Check telemetry configuration to determine logging behavior
        telemetry_config = ensure_telemetry_consent()

        # Extract context for structured logging
        context = _get_exception_context(exc_type, exc_value, tb)

        # Always send to telemetry backend if enabled (regardless of debug mode)
        if telemetry_config.enabled:
            # Get the OpenTelemetry handler for backend logging
            otel_handler = get_otel_logging_handler()
            if otel_handler:
                # Create a separate logger that only sends to OTEL backend
                import logging

                telemetry_logger = logging.getLogger("codegen.telemetry.exceptions")
                telemetry_logger.setLevel(logging.ERROR)

                # Remove any existing handlers to avoid console output
                telemetry_logger.handlers.clear()
                telemetry_logger.addHandler(otel_handler)
                telemetry_logger.propagate = False  # Don't propagate to parent loggers

                # Log to telemetry backend only
                telemetry_logger.error(f"Unhandled CLI exception: {exc_type.__name__}: {exc_value}", extra=context, exc_info=(exc_type, exc_value, tb))

        # Only log to console if debug mode is enabled
        if telemetry_config.debug:
            logger.error(f"Unhandled CLI exception: {exc_type.__name__}: {exc_value}", extra=context, exc_info=(exc_type, exc_value, tb))
            logger.debug("Exception details logged for telemetry", extra={"operation": "cli.exception_logging", "session_id": get_session_uuid()})

    except Exception as logging_error:
        # If logging itself fails, at least print to stderr in debug mode or if telemetry is disabled
        try:
            telemetry_config = ensure_telemetry_consent()
            if telemetry_config.debug or not telemetry_config.enabled:
                print(f"Failed to log exception: {logging_error}", file=sys.stderr)
                print(f"Original exception: {exc_type.__name__}: {exc_value}", file=sys.stderr)
        except Exception:
            # If even the telemetry config check fails, always print to stderr
            print(f"Failed to log exception: {logging_error}", file=sys.stderr)
            print(f"Original exception: {exc_type.__name__}: {exc_value}", file=sys.stderr)

    # Always call the original excepthook to preserve normal error handling behavior
    _original_excepthook(exc_type, exc_value, tb)


def setup_global_exception_logging() -> None:
    """Set up global exception logging by installing the custom excepthook.

    This should be called early in the CLI initialization to ensure all unhandled
    exceptions are captured and logged.
    """
    # Only install if not already installed (avoid double installation)
    if sys.excepthook != global_exception_handler:
        sys.excepthook = global_exception_handler

        # Only log setup message to console if debug mode is enabled
        try:
            telemetry_config = ensure_telemetry_consent()
            if telemetry_config.debug:
                logger.debug("Global exception logging enabled", extra={"operation": "cli.exception_logging_setup", "session_id": get_session_uuid()})
        except Exception:
            # If we can't check telemetry config, silently continue
            pass


def teardown_global_exception_logging() -> None:
    """Restore the original exception handler.

    This can be called during cleanup to restore normal exception handling.
    """
    if sys.excepthook == global_exception_handler:
        sys.excepthook = _original_excepthook

        # Only log teardown message to console if debug mode is enabled
        try:
            telemetry_config = ensure_telemetry_consent()
            if telemetry_config.debug:
                logger.debug("Global exception logging disabled", extra={"operation": "cli.exception_logging_teardown", "session_id": get_session_uuid()})
        except Exception:
            # If we can't check telemetry config, silently continue
            pass
