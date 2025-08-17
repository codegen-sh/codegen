"""Repository utilities for managing repository ID resolution and environment variables."""

import os
from typing import Dict, List, Any

from rich.console import Console

console = Console()


def resolve_repo_id(explicit_repo_id: int | None = None) -> int | None:
    """Resolve repository ID with fallback strategy.
    
    Order of precedence:
    1) explicit_repo_id passed by the caller
    2) CODEGEN_REPO_ID environment variable
    3) REPOSITORY_ID environment variable
    
    Returns None if not found.
    """
    if explicit_repo_id is not None:
        return explicit_repo_id

    # Check CODEGEN_REPO_ID environment variable
    env_val = os.environ.get("CODEGEN_REPO_ID")
    if env_val is not None and env_val != "":
        try:
            return int(env_val)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid CODEGEN_REPO_ID value: {env_val}")
            return None

    # Check REPOSITORY_ID environment variable
    repo_id_env = os.environ.get("REPOSITORY_ID")
    if repo_id_env is not None and repo_id_env != "":
        try:
            return int(repo_id_env)
        except ValueError:
            console.print(f"[red]Error:[/red] Invalid REPOSITORY_ID value: {repo_id_env}")
            return None

    return None


def get_current_repo_id() -> int | None:
    """Get the current repository ID from environment variables."""
    return resolve_repo_id()


def get_repo_env_status() -> Dict[str, str]:
    """Get the status of repository-related environment variables."""
    return {
        "CODEGEN_REPO_ID": os.environ.get("CODEGEN_REPO_ID", "Not set"),
        "REPOSITORY_ID": os.environ.get("REPOSITORY_ID", "Not set"),
    }


def set_repo_env_variable(repo_id: int, var_name: str = "CODEGEN_REPO_ID") -> bool:
    """Set repository ID in environment variable.
    
    Args:
        repo_id: Repository ID to set
        var_name: Environment variable name (default: CODEGEN_REPO_ID)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        os.environ[var_name] = str(repo_id)
        return True
    except Exception as e:
        console.print(f"[red]Error setting {var_name}:[/red] {e}")
        return False


def clear_repo_env_variables() -> None:
    """Clear all repository-related environment variables."""
    env_vars = ["CODEGEN_REPO_ID", "REPOSITORY_ID"]
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]


def update_env_file_with_repo(repo_id: int, env_file_path: str = ".env") -> bool:
    """Update .env file with repository ID."""
    try:
        lines = []
        key_updated = False
        key_to_update = "CODEGEN_REPO_ID"
        
        # Read existing .env file if it exists
        if os.path.exists(env_file_path):
            with open(env_file_path, "r") as f:
                lines = f.readlines()
        
        # Update or add the key
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key_to_update}="):
                lines[i] = f"{key_to_update}={repo_id}\n"
                key_updated = True
                break
        
        # If key wasn't found, add it
        if not key_updated:
            if lines and not lines[-1].endswith('\n'):
                lines.append('\n')
            lines.append(f"{key_to_update}={repo_id}\n")
        
        # Write back to file
        with open(env_file_path, "w") as f:
            f.writelines(lines)
        
        return True
        
    except Exception as e:
        console.print(f"[red]Error updating .env file:[/red] {e}")
        return False


def get_repo_display_info() -> List[Dict[str, str]]:
    """Get repository information for display in TUI."""
    repo_id = get_current_repo_id()
    env_status = get_repo_env_status()
    
    info = []
    
    # Current repository ID
    if repo_id:
        info.append({
            "label": "Current Repository ID",
            "value": str(repo_id),
            "status": "active"
        })
    else:
        info.append({
            "label": "Current Repository ID", 
            "value": "Not configured",
            "status": "inactive"
        })
    
    # Environment variables status
    for var_name, value in env_status.items():
        info.append({
            "label": f"{var_name}",
            "value": value,
            "status": "active" if value != "Not set" else "inactive"
        })
    
    return info


def fetch_repositories_for_org(org_id: int) -> List[Dict[str, Any]]:
    """Fetch repositories for an organization.
    
    Args:
        org_id: Organization ID to fetch repositories for
        
    Returns:
        List of repository dictionaries
    """
    try:
        import requests
        from codegen.cli.api.endpoints import API_ENDPOINT
        from codegen.cli.auth.token_manager import get_current_token
        
        token = get_current_token()
        if not token:
            return []
            
        headers = {"Authorization": f"Bearer {token}"}
        
        # Try the repository endpoint (may not exist yet)
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{org_id}/repositories"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return data.get("items", [])
        else:
            # API endpoint doesn't exist yet, return mock data for demo
            return get_mock_repositories()
            
    except Exception:
        # If API fails, return mock data
        return get_mock_repositories()


def get_mock_repositories() -> List[Dict[str, Any]]:
    """Get mock repository data for demonstration.
    
    Returns:
        List of mock repository dictionaries
    """
    return [
        {"id": 1, "name": "codegen-sdk", "description": "Codegen SDK repository"},
        {"id": 2, "name": "web-frontend", "description": "Frontend web application"},
        {"id": 3, "name": "api-backend", "description": "Backend API service"},
        {"id": 4, "name": "mobile-app", "description": "Mobile application"},
        {"id": 5, "name": "docs-site", "description": "Documentation website"},
        {"id": 6, "name": "cli-tools", "description": "Command line tools"},
        {"id": 7, "name": "data-pipeline", "description": "Data processing pipeline"},
        {"id": 8, "name": "ml-models", "description": "Machine learning models"},
    ]


def ensure_repositories_cached(org_id: int | None = None) -> List[Dict[str, Any]]:
    """Ensure repositories are cached for the given organization.
    
    Args:
        org_id: Organization ID (will resolve if not provided)
        
    Returns:
        List of cached repositories
    """
    from codegen.cli.auth.token_manager import get_cached_repositories, cache_repositories
    from codegen.cli.utils.org import resolve_org_id
    
    # Get cached repositories first
    cached_repos = get_cached_repositories()
    if cached_repos:
        return cached_repos
    
    # If no cache, try to fetch from API
    if org_id is None:
        org_id = resolve_org_id()
    
    if org_id:
        repositories = fetch_repositories_for_org(org_id)
        if repositories:
            cache_repositories(repositories)
            return repositories
    
    # Fallback to mock data
    mock_repos = get_mock_repositories()
    cache_repositories(mock_repos)
    return mock_repos