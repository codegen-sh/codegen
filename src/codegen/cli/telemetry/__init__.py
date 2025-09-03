"""CLI telemetry module for analytics and observability."""

from codegen.cli.telemetry.consent import (
    ensure_telemetry_consent,
    update_telemetry_consent,
)
from codegen.cli.telemetry.exception_logger import (
    setup_global_exception_logging,
    teardown_global_exception_logging,
)

__all__ = [
    "ensure_telemetry_consent",
    "setup_global_exception_logging",
    "teardown_global_exception_logging",
    "update_telemetry_consent",
]
