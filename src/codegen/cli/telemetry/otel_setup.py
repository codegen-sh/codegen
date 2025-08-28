"""Simple OpenTelemetry logging setup for CLI telemetry.

This module provides a clean, minimal setup for sending CLI logs to the
OTLP collector when telemetry is enabled by the user.
"""

import logging
import os
import platform
import subprocess
import sys
import uuid
from typing import Any

from opentelemetry import _logs as logs
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource

from codegen import __version__
from codegen.cli.api.modal import get_modal_prefix
from codegen.cli.auth.token_manager import TokenManager
from codegen.cli.env.enums import Environment
from codegen.cli.env.global_env import global_env
from codegen.cli.utils.org import resolve_org_id
from codegen.configs.models.telemetry import TelemetryConfig

# Global logger provider instance
_logger_provider: LoggerProvider | None = None

# Global session UUID for this CLI invocation
_session_uuid: str = str(uuid.uuid4())


def _get_otlp_logs_endpoint() -> tuple[str, dict[str, str]]:
    """Get the OTLP logs endpoint and headers based on environment.

    This replicates the backend logic for determining the correct collector endpoint
    based on whether we're running in Kubernetes or Modal environment.

    Returns:
        Tuple of (endpoint_url, headers_dict)
    """
    # Check if we're running in Kubernetes by looking for K8S_POD_NAME env var
    k8s_pod_name = os.environ.get("K8S_POD_NAME")
    if k8s_pod_name:
        # Running in Kubernetes - use Grafana Alloy
        return "http://grafana-monitoring-staging-alloy-receiver.monitoring.svc.cluster.local:4318/v1/logs", {}

    # Running in Modal - use Modal OTEL collector
    modal_prefix = get_modal_prefix()
    suffix = "otel-collector.modal.run"

    if global_env.ENV == Environment.PRODUCTION:
        collector_endpoint = f"https://{modal_prefix}--{suffix}/cli/v1/logs"
    elif global_env.ENV == Environment.STAGING:
        collector_endpoint = f"https://{modal_prefix}--{suffix}/cli/v1/logs"
    else:  # DEVELOPMENT
        collector_endpoint = f"https://{modal_prefix}--{suffix}/cli/v1/logs"

    # Create basic auth header for Modal collector
    token_manager = TokenManager()
    token = token_manager.get_token()
    if not token:
        # Return empty headers if no auth configured
        return collector_endpoint, {}

    return collector_endpoint, {"Authorization": f"Bearer {token}"}


def _get_claude_info() -> dict[str, str]:
    """Get Claude Code path and version information quickly."""
    claude_info = {}

    try:
        # Use the same logic as the Claude command to find the CLI
        # Import here to avoid circular imports
        try:
            from codegen.cli.commands.claude.utils import resolve_claude_path

            claude_path = resolve_claude_path()
        except ImportError:
            # Fallback to basic path detection if utils not available
            claude_path = None

            # Quick check in PATH first
            import shutil

            claude_path = shutil.which("claude")

            # If not found, check common local paths
            if not claude_path:
                local_path = os.path.expanduser("~/.claude/local/claude")
                if os.path.isfile(local_path) and os.access(local_path, os.X_OK):
                    claude_path = local_path

        if claude_path:
            claude_info["claude.path"] = claude_path

            # Only get version if we found the path - use short timeout
            try:
                version_result = subprocess.run(
                    [claude_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=3,  # Short timeout for telemetry setup
                )
                if version_result.returncode == 0:
                    version_output = version_result.stdout.strip()
                    claude_info["claude.version"] = version_output if version_output else "unknown"
                else:
                    claude_info["claude.version"] = "check_failed"
            except (subprocess.TimeoutExpired, Exception):
                claude_info["claude.version"] = "check_timeout"
        else:
            claude_info["claude.available"] = "false"

    except Exception:
        # If anything fails, mark as error but don't break telemetry setup
        claude_info["claude.available"] = "detection_error"

    return claude_info


def _create_cli_resource(telemetry_config: TelemetryConfig) -> Resource:
    """Create OpenTelemetry resource with CLI-specific attributes."""
    global _session_uuid

    # Base service attributes
    resource_attributes: dict[str, Any] = {
        "service.name": "codegen-cli",
        "service.version": __version__,
        "session.id": _session_uuid,  # Unique UUID for this CLI invocation
        "os.type": platform.system().lower(),
        "os.version": platform.version(),
        "python.version": sys.version.split()[0],
    }

    # Add user context if logged in
    try:
        # Try to get the current user ID (if authenticated)
        auth_data = TokenManager().get_auth_data()
        if auth_data:
            user = auth_data.get("user")
            if user:
                resource_attributes["user.id"] = str(user.get("id"))

            organization = auth_data.get("organization")
            if organization:
                resource_attributes["organization.id"] = str(organization.get("id"))
                resource_attributes["cli_session_id"] = _session_uuid

    except Exception:
        # If user ID lookup fails, continue without it
        pass

    # Add organization context if available
    try:
        org_id = resolve_org_id()
        if org_id:
            resource_attributes["org.id"] = str(org_id)
    except Exception:
        # If org ID lookup fails, continue without it
        pass

    # Add environment context
    if os.environ.get("CI"):
        resource_attributes["deployment.environment"] = "ci"
    elif os.environ.get("CODESPACES"):
        resource_attributes["deployment.environment"] = "codespaces"
    elif os.environ.get("GITPOD_WORKSPACE_ID"):
        resource_attributes["deployment.environment"] = "gitpod"
    else:
        resource_attributes["deployment.environment"] = "local"

    # Add Claude Code information
    claude_info = _get_claude_info()
    resource_attributes.update(claude_info)

    return Resource.create(resource_attributes)


def setup_otel_logging() -> LoggerProvider | None:
    """Set up OpenTelemetry logging if telemetry is enabled.

    Returns:
        LoggerProvider if telemetry is enabled and setup succeeds, None otherwise
    """
    global _logger_provider

    # Return cached provider if already set up
    if _logger_provider is not None:
        return _logger_provider

    # Ensure telemetry consent and load configuration
    from codegen.cli.telemetry.consent import ensure_telemetry_consent

    telemetry_config = ensure_telemetry_consent()

    # Only set up if explicitly enabled
    if not telemetry_config.enabled:
        return None

    try:
        # Create resource with CLI metadata
        resource = _create_cli_resource(telemetry_config)

        # Create logger provider
        logger_provider = LoggerProvider(resource=resource)

        # Get OTLP endpoint and headers
        endpoint, headers = _get_otlp_logs_endpoint()

        # Create OTLP log exporter
        log_exporter = OTLPLogExporter(
            endpoint=endpoint,
            headers=headers,
            timeout=10,  # 10 second timeout
        )

        # Create batch processor for performance
        log_processor = BatchLogRecordProcessor(
            log_exporter,
            max_queue_size=1024,
            max_export_batch_size=256,
            export_timeout_millis=10000,  # 10 seconds
            schedule_delay_millis=2000,  # Export every 2 seconds
        )

        logger_provider.add_log_record_processor(log_processor)

        # Set as global provider
        logs.set_logger_provider(logger_provider)
        _logger_provider = logger_provider

        # Debug output if enabled
        if telemetry_config.debug:
            print(f"[Telemetry] Logging initialized with endpoint: {endpoint}")
            print(f"[Telemetry] Session UUID: {_session_uuid}")
            # Show key resource attributes
            resource_attrs = resource.attributes
            if "user.id" in resource_attrs:
                print(f"[Telemetry] User ID: {resource_attrs['user.id']}")
            if "org.id" in resource_attrs:
                print(f"[Telemetry] Org ID: {resource_attrs['org.id']}")
            if "claude.path" in resource_attrs:
                print(f"[Telemetry] Claude Path: {resource_attrs['claude.path']}")
            if "claude.version" in resource_attrs:
                print(f"[Telemetry] Claude Version: {resource_attrs['claude.version']}")
            elif "claude.available" in resource_attrs:
                print(f"[Telemetry] Claude Available: {resource_attrs['claude.available']}")

        return logger_provider

    except Exception as e:
        if telemetry_config.debug:
            print(f"[Telemetry] Failed to initialize logging: {e}")
        return None


def get_otel_logging_handler() -> logging.Handler | None:
    """Get an OpenTelemetry logging handler.

    This handler will send logs to the OTLP collector when telemetry is enabled.

    Returns:
        LoggingHandler if telemetry is enabled, None otherwise
    """
    logger_provider = setup_otel_logging()
    if logger_provider is None:
        return None

    # Create handler that bridges Python logging to OpenTelemetry
    handler = LoggingHandler(level=logging.NOTSET, logger_provider=logger_provider)
    return handler


def get_session_uuid() -> str:
    """Get the session UUID for this CLI invocation.

    Returns:
        The session UUID string that uniquely identifies this CLI run
    """
    global _session_uuid
    return _session_uuid


def shutdown_otel_logging():
    """Gracefully shutdown OpenTelemetry logging and flush pending data."""
    global _logger_provider

    if _logger_provider is not None:
        try:
            # Type checker workaround: assert that provider is not None after the check
            assert _logger_provider is not None
            _logger_provider.shutdown()
        except Exception:
            pass  # Ignore shutdown errors
        _logger_provider = None
