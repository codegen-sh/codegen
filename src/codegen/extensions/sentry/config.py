"""Configuration for Sentry integration."""

import os
from typing import Optional

# Environment variable names
SENTRY_AUTH_TOKEN_ENV = "SENTRY_AUTH_TOKEN"
SENTRY_CODEGEN_INSTALLATION_UUID_ENV = "SENTRY_CODEGEN_INSTALLATION_UUID"
SENTRY_RAMP_INSTALLATION_UUID_ENV = "SENTRY_RAMP_INSTALLATION_UUID"

# Default values
DEFAULT_ORGANIZATION_SLUG = "codegen-sh"


def get_sentry_auth_token() -> Optional[str]:
    """Get the Sentry auth token from environment variables.

    Returns:
        The Sentry auth token, or None if not set.
    """
    return os.environ.get(SENTRY_AUTH_TOKEN_ENV)


def get_installation_uuid(organization_slug: str) -> Optional[str]:
    """Get the Sentry installation UUID for the specified organization.

    Args:
        organization_slug: The organization slug to get the installation UUID for.

    Returns:
        The Sentry installation UUID, or None if not set.
    """
    if organization_slug == "codegen-sh":
        return os.environ.get(SENTRY_CODEGEN_INSTALLATION_UUID_ENV)
    elif organization_slug == "ramp":
        return os.environ.get(SENTRY_RAMP_INSTALLATION_UUID_ENV)
    return None


def get_available_organizations() -> dict[str, Optional[str]]:
    """Get a dictionary of available organizations and their installation UUIDs.

    Returns:
        A dictionary mapping organization slugs to installation UUIDs.
    """
    orgs = {}

    codegen_uuid = os.environ.get(SENTRY_CODEGEN_INSTALLATION_UUID_ENV)
    if codegen_uuid:
        orgs["codegen-sh"] = codegen_uuid

    ramp_uuid = os.environ.get(SENTRY_RAMP_INSTALLATION_UUID_ENV)
    if ramp_uuid:
        orgs["ramp"] = ramp_uuid

    return orgs
