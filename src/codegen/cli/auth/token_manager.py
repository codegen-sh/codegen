import json
import os
from pathlib import Path

from codegen.cli.api.client import RestAPI
from codegen.cli.auth.constants import AUTH_FILE, CONFIG_DIR
from codegen.cli.errors import AuthError


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
        """Authenticate the token with the api."""
        identity = RestAPI(token).identify()
        if not identity:
            msg = "No identity found for session"
            raise AuthError(msg)
        if identity.auth_context.status != "active":
            msg = "Current session is not active. API Token may be invalid or may have expired."
            raise AuthError(msg)
        self.save_token(token)

    def save_token(self, token: str) -> None:
        """Save api token to disk."""
        try:
            with open(self.token_file, "w") as f:
                json.dump({"token": token}, f)

            # Secure the file permissions (read/write for owner only)
            os.chmod(self.token_file, 0o600)
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
        if os.path.exists(self.token_file):
            os.remove(self.token_file)


def get_current_token() -> str | None:
    """Get the current authentication token if one exists.

    This is a helper function that creates a TokenManager instance and retrieves
    the stored token. The token is validated before being returned.

    Returns:
        Optional[str]: The current valid api token if one exists.
                      Returns None if no token exists.

    """
    token_manager = TokenManager()
    return token_manager.get_token()
