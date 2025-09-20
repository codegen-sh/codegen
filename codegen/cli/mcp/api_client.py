"""API client management for the Codegen MCP server."""

import os

# Import API client components
try:
    from codegen_api_client import ApiClient, Configuration
    from codegen_api_client.api import AgentsApi, OrganizationsApi, UsersApi

    API_CLIENT_AVAILABLE = True
except ImportError:
    API_CLIENT_AVAILABLE = False

# Global API client instances
_api_client = None
_agents_api = None
_organizations_api = None
_users_api = None


def get_api_client():
    """Get or create the API client instance."""
    global _api_client, _agents_api, _organizations_api, _users_api

    if not API_CLIENT_AVAILABLE:
        msg = "codegen-api-client is not available"
        raise RuntimeError(msg)

    if _api_client is None:
        # Configure the API client
        configuration = Configuration()

        # Set base URL from environment or use the CLI endpoint for consistency
        # Prefer explicit env override; else match API_ENDPOINT used by CLI commands
        from codegen.cli.api.endpoints import API_ENDPOINT
        base_url = os.getenv("CODEGEN_API_BASE_URL", API_ENDPOINT.rstrip("/"))
        configuration.host = base_url

        # Set authentication
        api_key = os.getenv("CODEGEN_API_KEY")
        if api_key:
            configuration.api_key = {"Authorization": f"Bearer {api_key}"}

        _api_client = ApiClient(configuration)
        _agents_api = AgentsApi(_api_client)
        _organizations_api = OrganizationsApi(_api_client)
        _users_api = UsersApi(_api_client)

    return _api_client, _agents_api, _organizations_api, _users_api


def is_api_client_available() -> bool:
    """Check if the API client is available."""
    return API_CLIENT_AVAILABLE
