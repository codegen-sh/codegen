"""Claude Code command with OpenTelemetry monitoring."""

import os
import signal
import subprocess
import sys
import threading
import time

import typer
from rich.console import Console

from .hooks import cleanup_claude_hook, ensure_claude_hook, get_codegen_url, wait_for_session_id
from codegen.cli.utils.org import resolve_org_id

console = Console()


def claude(
    org_id: int | None = typer.Option(None, help="Organization ID for telemetry endpoint (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)"),
    export_interval: int = typer.Option(60, help="Export interval in seconds (default: 60)"),
    log_prompts: bool = typer.Option(False, help="Log user prompt content (security consideration)"),
    console_output: bool = typer.Option(False, help="Output telemetry to console for debugging"),
    normal_mode: bool = typer.Option(False, help="Run Claude Code without telemetry (normal mode)"),
    debug_mode: bool = typer.Option(False, help="Show detailed debug information and run with verbose output"),
    debug_otel: bool = typer.Option(False, help="Show real-time OpenTelemetry events and where they're being sent"),
    debug_otel_actions_only: bool = typer.Option(False, help="Show only action-related OTLP events (tool usage, API calls) - cleaner than --debug-otel"),
    verbose_telemetry: bool = typer.Option(False, help="Enable detailed telemetry event logging in backend (default: disabled for cleaner logs)"),
):
    """Run Claude Code with OpenTelemetry monitoring and logging.

    This uses Claude Code's built-in OpenTelemetry support to monitor:
    - API requests and responses
    - Token usage and costs
    - Tool usage and decisions
    - Session metrics
    - User interactions
    """
    if normal_mode:
        console.print("🚀 Running Claude Code in normal mode (no telemetry)...", style="blue")
        try:
            subprocess.run(["claude"], check=True)
        except subprocess.CalledProcessError as e:
            console.print(f"❌ Error running Claude Code: {e}", style="red")
            raise typer.Exit(1)
        except FileNotFoundError:
            console.print("❌ Claude Code not found. Please install Claude Code first.", style="red")
            console.print("💡 Visit: https://claude.ai/download", style="dim")
            raise typer.Exit(1)
        return

    console.print("🔍 Starting Claude Code with remote telemetry monitoring...", style="bold blue")
    resolved_org_id = resolve_org_id(org_id)
    if resolved_org_id is None:
        console.print("[red]Error:[/red] Organization ID not provided. Pass --org-id, set CODEGEN_ORG_ID, or REPOSITORY_ORG_ID.")
        raise typer.Exit(1)
    console.print(f"📊 Sending telemetry to organization {resolved_org_id}", style="dim")

    # Set up Claude hook for session tracking
    if not ensure_claude_hook():
        console.print("⚠️  Failed to set up session tracking hook", style="yellow")

    # Set up environment variables for Claude Code OpenTelemetry
    env = os.environ.copy()

    # Enable telemetry (required)
    env["CLAUDE_CODE_ENABLE_TELEMETRY"] = "1"

    # Enable all telemetry features that might be disabled by default
    env["OTEL_METRICS_INCLUDE_SESSION_ID"] = "true"
    env["OTEL_METRICS_INCLUDE_ACCOUNT_UUID"] = "true"
    env["OTEL_METRICS_INCLUDE_VERSION"] = "true"

    # Configure OTLP exporters to send to your remote endpoint
    exporters = ["otlp"]
    console_exporters = []

    if console_output or debug_otel or debug_otel_actions_only:
        console_exporters.append("console")

    # For actions-only mode, disable metrics console output to reduce noise
    if debug_otel_actions_only:
        env["OTEL_METRICS_EXPORTER"] = "otlp"  # Only send metrics to remote, not console
        env["OTEL_LOGS_EXPORTER"] = ",".join(["otlp", *console_exporters])  # Logs to both
        console.print("🔇 Metrics console output disabled to reduce noise", style="dim")
    else:
        env["OTEL_METRICS_EXPORTER"] = ",".join(exporters)
        env["OTEL_LOGS_EXPORTER"] = ",".join(exporters)

    # Configure OTLP endpoint to your remote API
    from codegen.cli.api.endpoints import API_ENDPOINT
    from codegen.cli.auth.token_manager import get_current_token

    # Set OTLP endpoint to your telemetry API
    # Note: Claude Code will automatically append /v1/metrics and /v1/logs to this base URL
    otlp_endpoint = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/telemetry"
    env["OTEL_EXPORTER_OTLP_ENDPOINT"] = otlp_endpoint
    env["OTEL_EXPORTER_OTLP_PROTOCOL"] = "http/json"

    # Add authentication using your current token
    token = get_current_token()
    headers = []
    if token:
        headers.append(f"Authorization=Bearer {token}")
        console.print("🔐 Using stored authentication token", style="dim")
    else:
        console.print("⚠️  No authentication token found. Telemetry may fail.", style="yellow")
        console.print("💡 Run 'codegen login' first", style="dim")

    # Add verbose telemetry flag
    if verbose_telemetry:
        headers.append("X-Verbose-Telemetry=true")
        console.print("🔍 Enabled verbose telemetry logging", style="dim")
    else:
        console.print("🔇 Disabled verbose telemetry logging (use --verbose-telemetry to enable)", style="dim")

    if headers:
        env["OTEL_EXPORTER_OTLP_HEADERS"] = ",".join(headers)

    # Set export intervals (in milliseconds)
    try:
        interval_ms = max(1, int(export_interval)) * 1000
    except Exception:
        interval_ms = 60000
    env["OTEL_METRIC_EXPORT_INTERVAL"] = str(interval_ms)
    env["OTEL_LOGS_EXPORT_INTERVAL"] = str(interval_ms)

    # Enable verbose OTLP debugging if requested
    if debug_otel or debug_otel_actions_only:
        env["OTEL_LOG_LEVEL"] = "DEBUG"
        env["OTEL_EXPORTER_OTLP_DEBUG"] = "true"
        env["OTEL_PYTHON_LOG_CORRELATION"] = "true"

        # Additional info for actions-only mode
        if debug_otel_actions_only:
            console.print("🎯 OTLP Debug: Actions-only mode enabled (metrics output filtered)", style="yellow")

    # Log user prompts if requested (security consideration)
    # Also enable for debug_otel modes to help with troubleshooting
    if log_prompts or debug_otel or debug_otel_actions_only:
        env["OTEL_LOG_USER_PROMPTS"] = "1"
        if (debug_otel or debug_otel_actions_only) and not log_prompts:
            console.print("🐛 User prompt content logging ENABLED for debugging", style="yellow")
        else:
            console.print("⚠️  User prompt content logging is ENABLED", style="yellow")
    else:
        env["OTEL_LOG_USER_PROMPTS"] = "0"  # Explicitly disable
        console.print("🔒 User prompt content is redacted (only length tracked)", style="dim")

    # Add resource attributes for identification
    resource_attrs = [
        "service.name=claude-code",
        "service.version=monitored",
        "deployment.environment=development",
        f"organization.id={resolved_org_id}",
        f"user.id={token}" if token else "user.id=unauthenticated",
    ]
    env["OTEL_RESOURCE_ATTRIBUTES"] = ",".join(resource_attrs)

    # Optional: Reduce cardinality for better performance
    # env["OTEL_METRICS_INCLUDE_SESSION_ID"] = "false"

    # Test if Claude Code is accessible first
    console.print("🔍 Testing Claude Code accessibility...", style="blue")
    try:
        test_result = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=10)
        if test_result.returncode == 0:
            console.print(f"✅ Claude Code found: {test_result.stdout.strip()}", style="green")
        else:
            console.print(f"⚠️  Claude Code test failed with code {test_result.returncode}", style="yellow")
            if test_result.stderr:
                console.print(f"Error: {test_result.stderr.strip()}", style="red")
    except subprocess.TimeoutExpired:
        console.print("⚠️  Claude Code version check timed out", style="yellow")
    except Exception as e:
        console.print(f"⚠️  Claude Code test error: {e}", style="yellow")

    console.print("🚀 Launching Claude Code with OpenTelemetry...", style="blue")

    # Debug output for telemetry configuration
    if debug_mode or console_output or debug_otel:
        console.print(f"[dim]Debug: OTLP Endpoint: {otlp_endpoint}[/dim]")
        console.print(f"[dim]Debug: Metrics URL: {otlp_endpoint}/v1/metrics[/dim]")
        console.print(f"[dim]Debug: Logs URL: {otlp_endpoint}/v1/logs[/dim]")
        console.print(f"[dim]Debug: Organization ID: {resolved_org_id}[/dim]")
        console.print(f"[dim]Debug: Resource Attributes: {','.join(resource_attrs)}[/dim]")

        if debug_otel:
            console.print("[yellow]🐛 OTLP Debug Mode: Real-time telemetry events will be shown[/yellow]")
            console.print("[dim]Export interval: 5 seconds (faster for debugging)[/dim]")
            console.print("[dim]User prompts: enabled for debugging[/dim]")
            console.print("[dim]Console export: enabled to see local events[/dim]")

        # Show key environment variables being set
        console.print("[dim]Debug: Key environment variables:[/dim]")
        otel_vars = {k: v for k, v in env.items() if k.startswith("OTEL_") or k.startswith("CLAUDE_CODE_")}
        for key, value in otel_vars.items():
            if "HEADERS" in key and token:
                # Mask the token for security
                console.print(f"[dim]  {key}=Authorization=Bearer ***[/dim]")
            else:
                console.print(f"[dim]  {key}={value}[/dim]")

    # Create a panel with telemetry information
    # Show minimal output unless in verbose mode
    if console_output or debug_mode or debug_otel:
        # Show detailed info only in debug modes
        console.print(f"🌐 Telemetry endpoint: {otlp_endpoint}/v1/{{metrics|logs}}", style="dim")
        console.print(f"🎯 Organization ID: {resolved_org_id}", style="dim")
        console.print(f"⏱️  Export interval: {export_interval} seconds", style="dim")
    else:
        # Minimal output - we'll update with session ID once we have it
        console.print("🔵 Starting Claude Code session...", style="blue")

    try:
        # Launch Claude Code with telemetry enabled
        if console_output or debug_mode or debug_otel:
            # Run Claude Code with visible output - telemetry will appear in console
            if debug_otel:
                console.print("🐛 Running Claude Code with OTLP debug output - you'll see real-time telemetry events...\n", style="yellow")
                console.print("📡 Look for HTTP requests to your telemetry API endpoints\n", style="dim")
                console.print("💡 Try asking Claude Code a question or making a file edit to generate events\n", style="dim")
            else:
                console.print("📺 Running Claude Code with visible output for debugging...\n", style="dim")
            process = subprocess.Popen(["claude"], env=env)
        else:
            # Run Claude Code in interactive mode but capture output for error handling
            console.print("🎯 Running Claude Code in interactive mode with remote telemetry...\n", style="dim")
            console.print("💡 Claude Code will start normally - telemetry data is being sent to your API\n", style="dim")
            # Don't capture stdout/stderr - let Claude Code run normally
            process = subprocess.Popen(["claude"], env=env)

        # Start monitoring for session ID in a background thread
        session_id = None
        session_url_printed = False

        def monitor_session():
            nonlocal session_id, session_url_printed
            # Give Claude a moment to start up
            time.sleep(2.0)
            session_id = wait_for_session_id(timeout=30.0)  # Wait up to 30 seconds
            if session_id and not session_url_printed:
                url = get_codegen_url(session_id)
                console.print(f"\n🔵 Codegen URL: {url}\n", style="bold blue")
                session_url_printed = True

        # Start session monitoring in background
        session_thread = threading.Thread(target=monitor_session, daemon=True)
        session_thread.start()

        # Handle Ctrl+C gracefully
        def signal_handler(signum, frame):
            console.print("\n🛑 Stopping Claude Code and telemetry collection...", style="yellow")
            process.terminate()
            cleanup_claude_hook()  # Clean up our hook
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Wait for Claude Code to finish
        returncode = process.wait()

        if returncode != 0:
            console.print(f"❌ Claude Code exited with error code {returncode}", style="red")
        else:
            console.print("✅ Claude Code finished successfully", style="green")

    except FileNotFoundError:
        console.print("❌ Claude Code not found. Please install Claude Code first.", style="red")
        console.print("💡 Visit: https://claude.ai/download", style="dim")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n🛑 Interrupted by user", style="yellow")
    except Exception as e:
        console.print(f"❌ Error running Claude Code: {e}", style="red")
        raise typer.Exit(1)
    finally:
        # Clean up hook
        cleanup_claude_hook()

        if session_id:
            url = get_codegen_url(session_id)
            console.print(f"\n🔵 Session URL: {url}", style="bold blue")

        console.print(f"📊 Telemetry data was sent to: {otlp_endpoint}/v1/{{metrics|logs}}", style="dim")
        console.print(f"🎯 Organization ID: {resolved_org_id}", style="dim")
        console.print("💡 Check your backend logs to see the processed telemetry data", style="dim")
        console.print("📖 Claude Code docs: https://docs.anthropic.com/en/docs/claude-code/monitoring-usage", style="dim")
