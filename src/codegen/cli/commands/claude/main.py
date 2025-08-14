"""Claude Code command with session tracking."""

import os
import signal
import subprocess
import sys
import threading
import time

import typer
from codegen.cli.commands.claude.claude_log_watcher import ClaudeLogWatcherManager
from codegen.cli.commands.claude.claude_session_api import end_claude_session, generate_session_id
from codegen.cli.commands.claude.config.mcp_setup import add_codegen_mcp_server, cleanup_codegen_mcp_server
from codegen.cli.commands.claude.hooks import cleanup_claude_hook, ensure_claude_hook, get_codegen_url
from codegen.cli.commands.claude.quiet_console import console
from codegen.cli.utils.org import resolve_org_id


def claude(
    org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)"),
    no_mcp: bool | None = typer.Option(False, "--no-mcp", help="Disable Codegen's MCP server with additional capabilities over HTTP"),
):
    """Run Claude Code with session tracking.

    This command runs Claude Code and tracks the session in the backend API:
    - Generates a unique session ID
    - Creates an agent run when Claude starts
    - Updates the agent run status when Claude exits
    """
    # Generate session ID for tracking
    session_id = generate_session_id()
    console.print(f"🆔 Generated session ID: {session_id[:8]}...", style="dim")
    
    # Resolve org_id early for session management
    resolved_org_id = resolve_org_id(org_id)
    if resolved_org_id is None:
        console.print("[red]Error:[/red] Organization ID not provided. Pass --org-id, set CODEGEN_ORG_ID, or REPOSITORY_ORG_ID.")
        raise typer.Exit(1)
    
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
            poll_interval=1.0,  # Check every second
            on_log_entry=None
        )
        
        if not log_watcher_started:
            console.print("⚠️  Failed to start log watcher", style="yellow")

        # Handle Ctrl+C gracefully
        def signal_handler(signum, frame):
            console.print("\n🛑 Stopping Claude Code...", style="yellow")
            log_watcher_manager.stop_all_watchers()  # Stop log watchers
            process.terminate()
            cleanup_claude_hook()  # Clean up our hook
            cleanup_codegen_mcp_server() # Clean up MCP Server
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