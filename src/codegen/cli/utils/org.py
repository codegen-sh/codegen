"""Organization resolution utilities for CLI commands."""

import os
import time

import requests

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_org_id, get_current_token
from codegen.cli.commands.claude.quiet_console import console

# Cache for org resolution to avoid repeated API calls
_org_cache = {}
_cache_timeout = 300  # 5 minutes


def resolve_org_id(explicit_org_id: int | None = None) -> int | None:
    """Resolve the organization id from CLI input or environment.

    Order of precedence:
    1) explicit_org_id passed by the caller
    2) CODEGEN_ORG_ID environment variable (dotenv is loaded by global_env)

    Returns None if not found.
    """
    global _org_cache

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

        # Try stored org ID from auth data (fast, no API call)
        stored_org_id = get_current_org_id()
        if stored_org_id:
            return stored_org_id

        # Attempt auto-detection via API: if user belongs to organizations, use the first
        try:
            token = get_current_token()
            if not token:
                print("No token found")
                return None

            # Check cache first
            cache_key = f"org_auto_detect_{token[:10]}"  # Use first 10 chars as key
            current_time = time.time()

            if cache_key in _org_cache:
                cached_data, cache_time = _org_cache[cache_key]
                if current_time - cache_time < _cache_timeout:
                    return cached_data

            headers = {"Authorization": f"Bearer {token}"}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items") or []

            org_id = None
            if isinstance(items, list) and len(items) >= 1:
                org = items[0]
                org_id_raw = org.get("id")
                try:
                    org_id = int(org_id_raw)
                except Exception:
                    org_id = None

            # Cache the result
            _org_cache[cache_key] = (org_id, current_time)
            return org_id

        except Exception as e:
            console.print(f"Exception: {e}")
            return None

    try:
        return int(env_val)
    except ValueError:
        return None
