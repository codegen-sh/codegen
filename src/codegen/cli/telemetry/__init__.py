"""CLI telemetry module for analytics and observability."""

from codegen.cli.telemetry.consent import (
    ensure_telemetry_consent,
    update_telemetry_consent,
)

__all__ = [
    "ensure_telemetry_consent",
    "update_telemetry_consent",
]
