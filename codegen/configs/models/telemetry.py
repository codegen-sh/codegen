"""Telemetry configuration for CLI usage analytics and debugging."""

from codegen.configs.models.base_config import BaseConfig


class TelemetryConfig(BaseConfig):
    """Configuration for CLI telemetry.

    Telemetry is opt-in by default and helps improve the CLI experience
    by collecting usage analytics, performance metrics, and error diagnostics.
    """

    # Whether telemetry is enabled (opt-in by default)
    enabled: bool = False

    # Whether user has been prompted for telemetry consent
    consent_prompted: bool = False

    # Anonymous user ID for telemetry correlation
    anonymous_id: str | None = None

    # Telemetry endpoint (defaults to production collector)
    endpoint: str | None = None

    # Debug mode for verbose telemetry logging
    debug: bool = False

    def __init__(self, env_filepath=None, **kwargs):
        super().__init__(prefix="TELEMETRY", env_filepath=env_filepath, **kwargs)
