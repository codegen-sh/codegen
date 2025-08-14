import json
import requests

from codegen.cli.api.endpoints import API_ENDPOINT

import requests

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id


def execute_tool_via_api(tool_name: str, arguments: dict):
    """Execute a tool via the Codegen API."""
    try:
        token = get_current_token()
        if not token:
            return {"error": "Not authenticated. Please run 'codegen login' first."}

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

        # Determine org id: prefer explicit in arguments, else resolve from env/config/API
        org_id = None
        if isinstance(arguments, dict):
            org_id = arguments.get("org_id")
        org_id = resolve_org_id(org_id)
        if org_id is None:
            return {"error": "Organization ID not provided. Include org_id argument, or set CODEGEN_ORG_ID/REPOSITORY_ORG_ID."}

        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{org_id}/tools/execute"

        payload = {"tool_name": tool_name, "arguments": arguments}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        return {"error": f"Error executing tool {tool_name}: {e}"}
