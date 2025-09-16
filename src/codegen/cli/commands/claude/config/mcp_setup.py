import subprocess

from codegen.cli.api.endpoints import MCP_SERVER_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.commands.claude.quiet_console import console
from codegen.cli.commands.claude.utils import resolve_claude_path


def add_codegen_mcp_server(org_id: int | None = None, repo_id: int | None = None):
    console.print("🔧 Configuring MCP server 'codegen-tools'...", style="blue")
    try:
        token = get_current_token()
        if not token:
            console.print("⚠️  No authentication token found. Please run 'codegen login' first.", style="yellow")
            return

        claude_path = resolve_claude_path()
        if not claude_path:
            console.print("⚠️  'claude' CLI not found to add MCP server", style="yellow")
            return

        # Build the command with required headers
        cmd = [
            claude_path,
            "mcp",
            "add",
            "--transport",
            "http",
            "codegen-tools",
            MCP_SERVER_ENDPOINT,
            "--header",
            f"Authorization: Bearer {token}",
        ]

        # Add organization ID header if available
        if org_id is not None:
            cmd.extend(["--header", f"x-organization-id: {org_id}"])
            console.print(f"  Adding organization ID: {org_id}", style="dim")

        # Add repository ID header if available
        if repo_id is not None:
            cmd.extend(["--header", f"x-repo-id: {repo_id}"])
            console.print(f"  Adding repository ID: {repo_id}", style="dim")

        add_result = subprocess.run(
            cmd,
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
        claude_path = resolve_claude_path()
        if not claude_path:
            # Silently skip if claude is not found during cleanup
            return

        subprocess.run(
            [
                claude_path,
                "mcp",
                "remove",
                "codegen-tools",
            ],
        )
    except Exception as e:
        console.print(f"⚠️  Error removing MCP server: {e}", style="yellow")
