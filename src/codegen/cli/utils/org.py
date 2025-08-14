"""Organization resolution utilities for CLI commands."""

import os
from typing import Optional

import requests

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.commands.claude.quiet_console import console

def resolve_org_id(explicit_org_id: Optional[int] = None) -> Optional[int]:
    """Resolve the organization id from CLI input or environment.

    Order of precedence:
    1) explicit_org_id passed by the caller
    2) CODEGEN_ORG_ID environment variable (dotenv is loaded by global_env)

    Returns None if not found.
    """

    if explicit_org_id is not None:
        return explicit_org_id

    env_val = os.environ.get("CODEGEN_ORG_ID")
    if env_val is None or env_val == "":
        # Try repository-scoped org id from .env
        repo_org = os.environ.get("REPOSITORY_ORG_ID")
        if repo_org:
            try:
                return int(repo_org)
            except ValueError:
                pass

        # Attempt auto-detection via API: if user belongs to organizations, use the first
        try:
            token = get_current_token()
            if not token:
                print("No token found")
                return None
            headers = {"Authorization": f"Bearer {token}"}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items") or []
            if isinstance(items, list) and len(items) >= 1:
                org = items[0]
                org_id = org.get("id")
                try:
                    return int(org_id)
                except Exception:
                    return None
            # None returned
            return None
        except Exception as e:
            console.print(f"Exception: {e}")
            return None

    try:
        return int(env_val)
    except ValueError:
        return None

