import asyncio
import json
import logging
import os
import platform
import shutil
from pathlib import Path

import requests


class Windsurf:
    def __init__(self, log_level=logging.INFO):
        """Initialize the Windsurf class for Codeium integration."""
        logging.basicConfig(level=log_level)
        self.logger = logging.getLogger("Windsurf")
        self.api_base_url = "https://api.codeium.com"
        self.user_data_path = self._get_user_data_path()

    def log(self, message, is_error=False):
        """Log messages with appropriate level."""
        if is_error:
            self.logger.error(message)
        else:
            self.logger.debug(message)

    def _get_user_data_path(self):
        """Get the path to Windsurf/Codeium user data based on platform."""
        if platform.system() == "Windows":
            return Path(os.environ.get("APPDATA", "")) / "Codeium"
        elif platform.system() == "Darwin":  # macOS
            return Path.home() / "Library" / "Application Support" / "Codeium"
        else:  # Linux and others
            return Path.home() / ".config" / "Codeium"

    def is_installed(self):
        """Check if Windsurf/Codeium is installed on the system.

        Returns:
            bool: True if installed, False otherwise
        """
        # Check if the user data directory exists
        if not self.user_data_path.exists():
            self.log("Codeium user data directory not found", True)
            return False

        # Check if auth file exists
        auth_path = self.get_auth_token_path()
        if not auth_path.exists():
            self.log("Codeium auth file not found", True)
            return False

        # Check if config file exists
        config_path = self.get_config_path()
        if not config_path.exists():
            self.log("Codeium config file not found", True)
            return False

        # Check if the Codeium binary is installed
        binary_path = self._get_binary_path()
        if binary_path and not binary_path.exists():
            self.log("Codeium binary not found", True)
            return False

        return True

    def _get_binary_path(self):
        """Get the path to the Codeium binary based on platform."""
        try:
            if platform.system() == "Windows":
                # Check in Program Files
                program_files = os.environ.get("ProgramFiles", "C:\\Program Files")
                path = Path(program_files) / "Codeium" / "Codeium.exe"
                if path.exists():
                    return path

                # Check in PATH
                codeium_path = shutil.which("codeium.exe")
                if codeium_path:
                    return Path(codeium_path)

            elif platform.system() == "Darwin":  # macOS
                # Check in Applications
                path = Path("/Applications/Codeium.app/Contents/MacOS/Codeium")
                if path.exists():
                    return path

                # Check in PATH
                codeium_path = shutil.which("codeium")
                if codeium_path:
                    return Path(codeium_path)

            else:  # Linux and others
                # Check in common locations
                paths = [Path("/usr/bin/codeium"), Path("/usr/local/bin/codeium"), Path(os.path.expanduser("~/.local/bin/codeium"))]

                for path in paths:
                    if path.exists():
                        return path

                # Check in PATH
                codeium_path = shutil.which("codeium")
                if codeium_path:
                    return Path(codeium_path)

            return None
        except Exception as e:
            self.log(f"Error finding Codeium binary: {e!s}", True)
            return None

    def get_config_path(self):
        """Get the path to the Codeium configuration file."""
        return self.user_data_path / "config.json"

    def get_auth_token_path(self):
        """Get the path to the authentication token file."""
        return self.user_data_path / "auth.json"

    def get_auth_token(self):
        """Read the authentication token from the auth file."""
        try:
            auth_path = self.get_auth_token_path()
            self.log(f"Reading auth token from: {auth_path}")

            if not auth_path.exists():
                self.log("Auth token file does not exist", True)
                return None

            with open(auth_path) as f:
                auth_data = json.load(f)

            if "api_key" in auth_data:
                return auth_data["api_key"]
            else:
                self.log("No API key found in auth data", True)
                return None

        except Exception as e:
            self.log(f"Error reading auth token: {e!s}", True)
            return None

    async def get_user_info(self):
        """Get user information using the auth token."""
        token = self.get_auth_token()
        if not token:
            return None

        try:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

            response = requests.get(f"{self.api_base_url}/user/info", headers=headers)
            if response.status_code == 200:
                self.log(f"User info response: {response.json()}")
                return response.json()
            else:
                self.log(f"Failed to get user info: {response.status_code}", True)
                return None

        except Exception as e:
            self.log(f"Error getting user info: {e!s}", True)
            return None

    async def validate_token(self):
        """Validate if the current token is valid."""
        user_info = await self.get_user_info()
        return user_info is not None


async def main():
    windsurf = Windsurf(log_level=logging.DEBUG)

    # Check if Codeium is installed
    if not windsurf.is_installed():
        print("Codeium is not installed or not properly configured")
        return

    token = windsurf.read_auth_token()
    print(f"Token: {token}")

    is_valid = await windsurf.validate_token()
    print(f"Token is valid: {is_valid}")


if __name__ == "__main__":
    # TODO: don't have windsurf at the moment, test later if feature is needed
    asyncio.run(main())
