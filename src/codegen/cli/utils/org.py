"""Organization resolution utilities for CLI commands."""

import os
import time

import requests

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import (
    get_cached_organizations,
    get_current_org_id,
    get_current_token,
    get_org_name_from_cache,
    is_org_id_cached,
)
from codegen.cli.commands.claude.quiet_console import console

# Cache for org resolution to avoid repeated API calls
_org_cache = {}
_cache_timeout = 300  # 5 minutes


def resolve_org_id(explicit_org_id: int | None = None) -> int | None:
    """Resolve organization ID with fallback strategy and cache validation.

    Order of precedence:
    1) explicit_org_id passed by the caller (validated against cache)
    2) CODEGEN_ORG_ID environment variable (validated against cache if available)
    3) REPOSITORY_ORG_ID environment variable (validated against cache if available)
    4) stored org ID from auth data (fast, no API call)
    5) API auto-detection (uses first organization from user's organizations)

    Returns None if not found.
    """
    global _org_cache

    def _validate_org_id_with_cache(org_id: int, source: str) -> int | None:
        """Validate an org ID against the cache and show helpful errors."""
        if is_org_id_cached(org_id):
            return org_id
        
        # If we have a cache but the org ID is not in it, show helpful error
        cached_orgs = get_cached_organizations()
        if cached_orgs:
            org_list = ", ".join([f"{org['name']} ({org['id']})" for org in cached_orgs])
            console.print(f"[red]Error:[/red] Organization ID {org_id} from {source} not found in your accessible organizations.")
            console.print(f"[yellow]Available organizations:[/yellow] {org_list}")
            return None
        
        # If no cache available, trust the org ID (will be validated by API)
        return org_id

    if explicit_org_id is not None:
        return _validate_org_id_with_cache(explicit_org_id, "command line")

    env_val = os.environ.get("CODEGEN_ORG_ID")
    if env_val is not None and env_val != "":
        try:
            env_org_id = int(env_val)
            return _validate_org_id_with_cache(env_org_id, "CODEGEN_ORG_ID")
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid CODEGEN_ORG_ID value: {env_val}")
            return None

    # Try repository-scoped org id from .env
    repo_org = os.environ.get("REPOSITORY_ORG_ID")
    if repo_org:
        try:
            repo_org_id = int(repo_org)
            return _validate_org_id_with_cache(repo_org_id, "REPOSITORY_ORG_ID")
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid REPOSITORY_ORG_ID value: {repo_org}")
            return None

    # Try stored org ID from auth data (fast, no API call)
    stored_org_id = get_current_org_id()
    if stored_org_id:
        return stored_org_id

    # Attempt auto-detection via API: if user belongs to organizations, use the first
    try:
        token = get_current_token()
        if not token:
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
        console.print(f"Error during organization auto-detection: {e}")
        return None
