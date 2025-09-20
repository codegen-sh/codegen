from enum import Enum

from codegen.cli.env.enums import Environment
from codegen.cli.env.global_env import global_env


class DomainRegistry(Enum):
    STAGING = "chadcode.sh"
    PRODUCTION = "codegen.com"
    LOCAL = "localhost:3000"


def get_domain() -> str:
    """Get the appropriate domain based on the current environment."""
    if global_env.ENV == Environment.PRODUCTION:
        return DomainRegistry.PRODUCTION.value
    elif global_env.ENV == Environment.STAGING:
        return DomainRegistry.STAGING.value
    else:
        return DomainRegistry.LOCAL.value


def generate_webapp_url(path: str = "", params: dict | None = None, protocol: str = "https") -> str:
    """Generate a complete URL for the web application.

    Args:
        path: The path component of the URL (without leading slash)
        params: Optional query parameters as a dictionary
        protocol: URL protocol (defaults to https, will be http for localhost)

    Returns:
        Complete URL string

    Example:
        generate_webapp_url("projects/123", {"tab": "settings"})
        # In staging: https://chadcode.sh/projects/123?tab=settings

    """
    domain = get_domain()
    # Use http for localhost
    if domain == DomainRegistry.LOCAL.value:
        protocol = "http"

    # Build base URL
    base_url = f"{protocol}://{domain}"

    # Add path if provided
    if path:
        path = path.lstrip("/")  # Remove leading slash if present
        base_url = f"{base_url}/{path}"

    # Add query parameters if provided
    if params:
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        base_url = f"{base_url}?{query_string}"

    return base_url
