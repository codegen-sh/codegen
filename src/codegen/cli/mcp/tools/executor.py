"""Tool execution logic for the Codegen MCP server."""

import requests

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token


def execute_tool_via_api(tool_name: str, arguments: dict):
    """Execute a tool via the Codegen API."""
    try:
        token = get_current_token()
        if not token:
            return {"error": "Not authenticated. Please run 'codegen login' first."}

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/11/tools/execute"

        payload = {"tool_name": tool_name, "arguments": arguments}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        return {"error": f"Error executing tool {tool_name}: {e}"}
