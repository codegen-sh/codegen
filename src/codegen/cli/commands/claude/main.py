"""Claude Code command with session tracking."""

import os
import signal
import subprocess
import sys

import requests
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.commands.claude.claude_log_watcher import ClaudeLogWatcherManager
from codegen.cli.commands.claude.claude_session_api import end_claude_session, generate_session_id
from codegen.cli.commands.claude.config.mcp_setup import add_codegen_mcp_server, cleanup_codegen_mcp_server
from codegen.cli.commands.claude.hooks import cleanup_claude_hook, ensure_claude_hook, get_codegen_url
from codegen.cli.commands.claude.quiet_console import console
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id

t_console = Console()


def _run_claude_background(resolved_org_id: int, prompt: str | None) -> None:
    """Create a background agent run with Claude context and exit."""
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    payload = {"prompt": prompt or "Start a Claude Code background session"}

    spinner = create_spinner("Creating agent run...")
    spinner.start()
    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "x-codegen-client": "codegen__claude_code",
        }
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/agent/run"
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        agent_run_data = response.json()
    finally:
        spinner.stop()

    run_id = agent_run_data.get("id", "Unknown")
    status = agent_run_data.get("status", "Unknown")
    web_url = agent_run_data.get("web_url", "")

    result_lines = [
        f"[cyan]Agent Run ID:[/cyan] {run_id}",
        f"[cyan]Status:[/cyan]       {status}",
    ]
    if web_url:
        result_lines.append(f"[cyan]Web URL:[/cyan]      {web_url}")

    t_console.print(
        Panel(
            "\n".join(result_lines),
            title="🤖 [bold]Background Agent Run Created[/bold]",
            border_style="green",
            box=box.ROUNDED,
            padding=(1, 2),
        )
    )
    t_console.print("\n[dim]💡 Track progress with:[/dim] [cyan]codegen agents[/cyan]")
    if web_url:
        t_console.print(f"[dim]🌐 View in browser:[/dim]  [link]{web_url}[/link]")


def _run_claude_interactive(resolved_org_id: int, no_mcp: bool | None) -> None:
    """Launch Claude Code with session tracking and log watching."""
    # Generate session ID for tracking
    session_id = generate_session_id()
    console.print(f"🆔 Generated session ID: {session_id[:8]}...", style="dim")

    console.print("🚀 Starting Claude Code with session tracking...", style="blue")
    console.print(f"🎯 Organization ID: {resolved_org_id}", style="dim")

    # Set up environment variables for hooks to access session information
    os.environ["CODEGEN_CLAUDE_SESSION_ID"] = session_id
    os.environ["CODEGEN_CLAUDE_ORG_ID"] = str(resolved_org_id)

    # Set up Claude hook for session tracking
    if not ensure_claude_hook():
        console.print("⚠️  Failed to set up session tracking hook", style="yellow")

    # Initialize log watcher manager
    log_watcher_manager = ClaudeLogWatcherManager()

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

    # If MCP endpoint provided, register MCP server via Claude CLI before launch
    if not no_mcp:
        add_codegen_mcp_server()

    console.print("🔵 Starting Claude Code session...", style="blue")

    try:
        # Launch Claude Code with our session ID
        console.print(f"🚀 Launching Claude Code with session ID: {session_id[:8]}...", style="blue")

        url = get_codegen_url(session_id)
        console.print(f"\n🔵 Codegen URL: {url}\n", style="bold blue")

        process = subprocess.Popen(["claude", "--session-id", session_id])

        # Start log watcher for the session
        console.print("📋 Starting log watcher...", style="blue")
        log_watcher_started = log_watcher_manager.start_watcher(
            session_id=session_id,
            org_id=resolved_org_id,
            poll_interval=1.0,
            on_log_entry=None,
        )

        if not log_watcher_started:
            console.print("⚠️  Failed to start log watcher", style="yellow")

        # Handle Ctrl+C gracefully
        def signal_handler(signum, frame):
            console.print("\n🛑 Stopping Claude Code...", style="yellow")
            log_watcher_manager.stop_all_watchers()
            process.terminate()
            cleanup_claude_hook()
            cleanup_codegen_mcp_server()
            end_claude_session(session_id, "ERROR", resolved_org_id)
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        # Wait for Claude Code to finish
        returncode = process.wait()

        # Handle session completion based on exit code
        session_status = "COMPLETE" if returncode == 0 else "ERROR"
        end_claude_session(session_id, session_status, resolved_org_id)

        if returncode != 0:
            console.print(f"❌ Claude Code exited with error code {returncode}", style="red")
        else:
            console.print("✅ Claude Code finished successfully", style="green")

    except FileNotFoundError:
        console.print("❌ Claude Code not found. Please install Claude Code first.", style="red")
        console.print("💡 Visit: https://claude.ai/download", style="dim")
        log_watcher_manager.stop_all_watchers()
        end_claude_session(session_id, "ERROR", resolved_org_id)
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n🛑 Interrupted by user", style="yellow")
        log_watcher_manager.stop_all_watchers()
        end_claude_session(session_id, "ERROR", resolved_org_id)
    except Exception as e:
        console.print(f"❌ Error running Claude Code: {e}", style="red")
        log_watcher_manager.stop_all_watchers()
        end_claude_session(session_id, "ERROR", resolved_org_id)
        raise typer.Exit(1)
    finally:
        # Clean up resources
        try:
            log_watcher_manager.stop_all_watchers()
        except Exception as e:
            console.print(f"⚠️  Error stopping log watchers: {e}", style="yellow")

        cleanup_claude_hook()

        # Show final session info
        url = get_codegen_url(session_id)
        console.print(f"\n🔵 Session URL: {url}", style="bold blue")
        console.print(f"🆔 Session ID: {session_id}", style="dim")
        console.print(f"🎯 Organization ID: {resolved_org_id}", style="dim")
        console.print("💡 Check your backend to see the session data", style="dim")


def claude(
    org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)"),
    no_mcp: bool | None = typer.Option(False, "--no-mcp", help="Disable Codegen's MCP server with additional capabilities over HTTP"),
    background: str | None = typer.Option(None, "--background", "-b", help="Create a background agent run with this prompt instead of launching Claude Code"),
):
    """Run Claude Code with session tracking or create a background run."""
    # Resolve org_id early for session management
    resolved_org_id = resolve_org_id(org_id)
    if resolved_org_id is None:
        console.print("[red]Error:[/red] Organization ID not provided. Pass --org-id, set CODEGEN_ORG_ID, or REPOSITORY_ORG_ID.")
        raise typer.Exit(1)

    if background is not None:
        # Use the value from --background as the prompt
        final_prompt = background
        _run_claude_background(resolved_org_id, final_prompt)
        return

    _run_claude_interactive(resolved_org_id, no_mcp)
