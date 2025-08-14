
import subprocess

from codegen.cli.api.endpoints import MCP_SERVER_ENDPOINT
from codegen.cli.commands.claude.quiet_console import console
from codegen.cli.auth.token_manager import get_current_token


def add_codegen_mcp_server():
    console.print("🔧 Configuring MCP server 'codegen-tools'...", style="blue")
    try:
        token = get_current_token()
        if not token:
            console.print("⚠️  No authentication token found. Please run 'codegen login' first.", style="yellow")
            return

        add_result = subprocess.run(
            [
                "claude",
                "mcp",
                "add",
                "--transport",
                "http",
                "codegen-tools",
                MCP_SERVER_ENDPOINT,
                "--header",
                f"Authorization: Bearer {token}",
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if add_result.returncode == 0:
            console.print("✅ MCP server added: codegen-tools -> http", style="green")
        else:
            stderr = add_result.stderr.strip() if add_result.stderr else add_result.stdout.strip()
            console.print(f"⚠️  Failed to add MCP server (code {add_result.returncode}): {stderr}", style="yellow")
    except subprocess.TimeoutExpired:
        console.print("⚠️  MCP server add timed out", style="yellow")
    except FileNotFoundError:
        console.print("⚠️  'claude' CLI not found to add MCP server", style="yellow")
    except Exception as e:
        console.print(f"⚠️  Error adding MCP server: {e}", style="yellow")


def cleanup_codegen_mcp_server():
    try:
        subprocess.run(
            [
                "claude",
                "mcp",
                "remove",
                "codegen-tools",
            ],
        )
    except Exception as e:
        console.print(f"⚠️  Error removing MCP server: {e}", style="yellow")