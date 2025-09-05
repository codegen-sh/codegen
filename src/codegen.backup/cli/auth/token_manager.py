import json
import os
from pathlib import Path

from codegen.cli.auth.constants import AUTH_FILE, CONFIG_DIR

# Simple cache to avoid repeated file I/O
_token_cache = None
_cache_mtime = None


class TokenManager:
    # Simple token manager to store and retrieve tokens.
    # This manager checks if the token is expired before retrieval.
    # TODO: add support for refreshing token and re authorization via supabase oauth
    def __init__(self):
        self.config_dir = CONFIG_DIR
        self.token_file = AUTH_FILE
        self._ensure_config_dir()

    def _ensure_config_dir(self):
        """Create config directory if it doesn't exist."""
        if not os.path.exists(self.config_dir):
            Path(self.config_dir).mkdir(parents=True, exist_ok=True)

    def authenticate_token(self, token: str) -> None:
        """Store the token locally and fetch organization info."""
        self.save_token_with_org_info(token)

    def save_token_with_org_info(self, token: str) -> None:
        """Save api token to disk along with organization info."""
        global _token_cache, _cache_mtime

        # First fetch organization info using the token
        try:
            import requests

            from codegen.cli.api.endpoints import API_ENDPOINT

            headers = {"Authorization": f"Bearer {token}"}

            # Test token by getting user info
            user_response = requests.get(f"{API_ENDPOINT.rstrip('/')}/v1/users/me", headers=headers, timeout=10)
            user_response.raise_for_status()
            user_data = user_response.json()

            # Get organizations
            org_response = requests.get(f"{API_ENDPOINT.rstrip('/')}/v1/organizations", headers=headers, timeout=10)
            org_response.raise_for_status()
            org_data = org_response.json()

            # Prepare auth data with org info
            auth_data = {
                "token": token,
                "user": {"id": user_data.get("id"), "email": user_data.get("email"), "full_name": user_data.get("full_name"), "github_username": user_data.get("github_username")},
            }

            # Add organization info if available
            orgs = org_data.get("items", [])
            if orgs and len(orgs) > 0:
                # Store ALL organizations in cache for local resolution
                all_orgs = [{"id": org.get("id"), "name": org.get("name")} for org in orgs]
                primary_org = orgs[0]  # Use first org as primary/default
                auth_data["organization"] = {"id": primary_org.get("id"), "name": primary_org.get("name"), "all_orgs": all_orgs}
                auth_data["organizations_cache"] = all_orgs  # Separate cache for easy access

        except requests.RequestException as e:
            # If we can't fetch org info, still save the token but without org data
            print(f"Warning: Could not fetch organization info: {e}")
            auth_data = {"token": token}
        except Exception as e:
            print(f"Warning: Error fetching user/org info: {e}")
            auth_data = {"token": token}

        # Save to file
        try:
            with open(self.token_file, "w") as f:
                json.dump(auth_data, f, indent=2)

            # Secure the file permissions (read/write for owner only)
            os.chmod(self.token_file, 0o600)

            # Invalidate cache
            _token_cache = None
            _cache_mtime = None
        except Exception as e:
            print(f"Error saving token: {e!s}")
            raise

    def save_token(self, token: str) -> None:
        """Save api token to disk (legacy method - just saves token)."""
        global _token_cache, _cache_mtime
        try:
            with open(self.token_file, "w") as f:
                json.dump({"token": token}, f)

            # Secure the file permissions (read/write for owner only)
            os.chmod(self.token_file, 0o600)

            # Invalidate cache
            _token_cache = None
            _cache_mtime = None
        except Exception as e:
            print(f"Error saving token: {e!s}")
            raise

    def get_token(self) -> str | None:
        """Retrieve token from disk if it exists and is valid."""
        try:
            if not os.access(self.config_dir, os.R_OK):
                return None

            if not os.path.exists(self.token_file):
                return None

            with open(self.token_file) as f:
                data = json.load(f)
                token = data.get("token")
                if not token:
                    return None

                return token

        except (KeyError, OSError) as e:
            print(e)
            return None

    def clear_token(self) -> None:
        """Remove stored token."""
        global _token_cache, _cache_mtime
        if os.path.exists(self.token_file):
            os.remove(self.token_file)
            # Invalidate cache
            _token_cache = None
            _cache_mtime = None

    def get_auth_data(self) -> dict | None:
        """Retrieve complete auth data from disk."""
        try:
            if not os.access(self.config_dir, os.R_OK):
                return None

            if not os.path.exists(self.token_file):
                return None

            with open(self.token_file) as f:
                return json.load(f)
        except Exception:
            return None

    def get_org_id(self) -> int | None:
        """Get the stored organization ID."""
        auth_data = self.get_auth_data()
        if auth_data and "organization" in auth_data:
            org_id = auth_data["organization"].get("id")
            if org_id:
                try:
                    return int(org_id)
                except (ValueError, TypeError):
                    return None
        return None

    def get_org_name(self) -> str | None:
        """Get the stored organization name."""
        auth_data = self.get_auth_data()
        if auth_data and "organization" in auth_data:
            return auth_data["organization"].get("name")
        return None

    def get_user_info(self) -> dict | None:
        """Get the stored user info."""
        auth_data = self.get_auth_data()
        if auth_data and "user" in auth_data:
            return auth_data["user"]
        return None

    def get_cached_organizations(self) -> list[dict] | None:
        """Get all cached organizations.

        Returns:
            List of organization dictionaries with 'id' and 'name' keys, or None if no cache.
        """
        auth_data = self.get_auth_data()
        if auth_data and "organizations_cache" in auth_data:
            return auth_data["organizations_cache"]
        # Fallback to legacy format
        if auth_data and "organization" in auth_data and "all_orgs" in auth_data["organization"]:
            return auth_data["organization"]["all_orgs"]
        return None

    def is_org_id_in_cache(self, org_id: int) -> bool:
        """Check if an organization ID exists in the local cache.

        Args:
            org_id: The organization ID to check

        Returns:
            True if the organization ID is found in cache, False otherwise.
        """
        cached_orgs = self.get_cached_organizations()
        if not cached_orgs:
            return False

        return any(org.get("id") == org_id for org in cached_orgs)

    def get_org_name_from_cache(self, org_id: int) -> str | None:
        """Get organization name from cache by ID.

        Args:
            org_id: The organization ID to look up

        Returns:
            Organization name if found in cache, None otherwise.
        """
        cached_orgs = self.get_cached_organizations()
        if not cached_orgs:
            return None

        for org in cached_orgs:
            if org.get("id") == org_id:
                return org.get("name")
        return None

    def set_default_organization(self, org_id: int, org_name: str) -> None:
        """Set the default organization in auth.json.

        Args:
            org_id: The organization ID to set as default
            org_name: The organization name
        """
        auth_data = self.get_auth_data()
        if not auth_data:
            msg = "No authentication data found. Please run 'codegen login' first."
            raise ValueError(msg)

        # Verify the org exists in cache
        if not self.is_org_id_in_cache(org_id):
            msg = f"Organization {org_id} not found in cache. Please run 'codegen login' to refresh."
            raise ValueError(msg)

        # Update the organization info
        auth_data["organization"] = {"id": org_id, "name": org_name, "all_orgs": auth_data.get("organization", {}).get("all_orgs", [])}

        # Save to file
        try:
            import json

            with open(self.token_file, "w") as f:
                json.dump(auth_data, f, indent=2)

            # Secure the file permissions (read/write for owner only)
            os.chmod(self.token_file, 0o600)

            # Invalidate cache
            global _token_cache, _cache_mtime
            _token_cache = None
            _cache_mtime = None
        except Exception as e:
            msg = f"Error saving default organization: {e}"
            raise ValueError(msg)


def get_current_token() -> str | None:
    """Get the current authentication token if one exists.

    This is a helper function that creates a TokenManager instance and retrieves
    the stored token. The token is validated before being returned.
    Uses a simple cache to avoid repeated file I/O.

    Returns:
        Optional[str]: The current valid api token if one exists.
                      Returns None if no token exists.

    """
    global _token_cache, _cache_mtime

    try:
        # Check if token file exists
        if not os.path.exists(AUTH_FILE):
            return None

        # Get file modification time
        current_mtime = os.path.getmtime(AUTH_FILE)

        # Use cache if file hasn't changed
        if _token_cache is not None and _cache_mtime == current_mtime:
            return _token_cache

        # Read token from file
        token_manager = TokenManager()
        token = token_manager.get_token()

        # Update cache
        _token_cache = token
        _cache_mtime = current_mtime

        return token
    except Exception:
        # Fall back to uncached version on any error
        token_manager = TokenManager()
        return token_manager.get_token()


def get_current_org_id() -> int | None:
    """Get the stored organization ID if available.

    Returns:
        Optional[int]: The organization ID if stored, None otherwise.
    """
    token_manager = TokenManager()
    return token_manager.get_org_id()


def get_current_org_name() -> str | None:
    """Get the stored organization name if available.

    Returns:
        Optional[str]: The organization name if stored, None otherwise.
    """
    token_manager = TokenManager()
    return token_manager.get_org_name()


def get_cached_organizations() -> list[dict] | None:
    """Get all cached organizations.

    Returns:
        List of organization dictionaries with 'id' and 'name' keys, or None if no cache.
    """
    token_manager = TokenManager()
    return token_manager.get_cached_organizations()


def is_org_id_cached(org_id: int) -> bool:
    """Check if an organization ID exists in the local cache.

    Args:
        org_id: The organization ID to check

    Returns:
        True if the organization ID is found in cache, False otherwise.
    """
    token_manager = TokenManager()
    return token_manager.is_org_id_in_cache(org_id)


def get_org_name_from_cache(org_id: int) -> str | None:
    """Get organization name from cache by ID.

    Args:
        org_id: The organization ID to look up

    Returns:
        Organization name if found in cache, None otherwise.
    """
    token_manager = TokenManager()
    return token_manager.get_org_name_from_cache(org_id)


def get_current_user_info() -> dict | None:
    """Get the stored user info if available.

    Returns:
        Optional[dict]: The user info if stored, None otherwise.
    """
    token_manager = TokenManager()
    return token_manager.get_user_info()


# Repository caching functions (similar to organization caching)


def get_cached_repositories() -> list[dict] | None:
    """Get all cached repositories.

    Returns:
        List of repository dictionaries with 'id' and 'name' keys, or None if no cache.
    """
    token_manager = TokenManager()
    auth_data = token_manager.get_auth_data()
    if auth_data and "repositories_cache" in auth_data:
        return auth_data["repositories_cache"]
    return None


def cache_repositories(repositories: list[dict]) -> None:
    """Cache repositories to local storage.

    Args:
        repositories: List of repository dictionaries to cache
    """
    token_manager = TokenManager()
    auth_data = token_manager.get_auth_data()
    if auth_data:
        auth_data["repositories_cache"] = repositories
        # Save back to file
        try:
            import json

            with open(token_manager.token_file, "w") as f:
                json.dump(auth_data, f, indent=2)
        except Exception:
            pass  # Fail silently


def is_repo_id_cached(repo_id: int) -> bool:
    """Check if a repository ID exists in the local cache.

    Args:
        repo_id: The repository ID to check

    Returns:
        True if the repository ID is found in cache, False otherwise.
    """
    cached_repos = get_cached_repositories()
    if not cached_repos:
        return False

    return any(repo.get("id") == repo_id for repo in cached_repos)


def get_repo_name_from_cache(repo_id: int) -> str | None:
    """Get repository name from cache by ID.

    Args:
        repo_id: The repository ID to look up

    Returns:
        Repository name if found in cache, None otherwise.
    """
    cached_repos = get_cached_repositories()
    if not cached_repos:
        return None

    for repo in cached_repos:
        if repo.get("id") == repo_id:
            return repo.get("name")

    return None


def get_current_repo_name() -> str | None:
    """Get the current repository name from environment or cache."""
    from codegen.cli.utils.repo import get_current_repo_id

    repo_id = get_current_repo_id()
    if repo_id:
        return get_repo_name_from_cache(repo_id)
    return None


def set_default_organization(org_id: int, org_name: str) -> None:
    """Set the default organization in auth.json.

    Args:
        org_id: The organization ID to set as default
        org_name: The organization name
    """
    token_manager = TokenManager()
    return token_manager.set_default_organization(org_id, org_name)
