"""Organizations API client for the Codegen SDK."""

from collections.abc import Iterator
from typing import Any

from codegen_api_client.api.organizations_api import OrganizationsApi
from codegen_api_client.api_client import ApiClient
from codegen_api_client.configuration import Configuration
from codegen_api_client.models.organization_response import OrganizationResponse
from codegen_api_client.rest import ApiException

from codegen.agents.constants import CODEGEN_BASE_API_URL
from codegen.exceptions import handle_api_error


class Organization:
    """Represents an organization with convenient access to its properties."""

    def __init__(self, data: OrganizationResponse):
        self._data = data

    @property
    def id(self) -> int:
        """Organization ID."""
        return self._data.id

    @property
    def name(self) -> str:
        """Organization name."""
        return self._data.name

    @property
    def settings(self) -> dict[str, Any]:
        """Organization settings."""
        return self._data.settings.to_dict() if self._data.settings else {}

    def to_dict(self) -> dict[str, Any]:
        """Convert organization to dictionary."""
        return self._data.to_dict()

    def __repr__(self) -> str:
        return f"Organization(id={self.id}, name='{self.name}')"


class Organizations:
    """API client for managing organizations in Codegen."""

    def __init__(self, token: str | None, base_url: str = CODEGEN_BASE_API_URL):
        """Initialize the Organizations client.

        Args:
            token: API authentication token
            base_url: Base URL for the API (defaults to production)
        """
        self.token = token

        # Configure API client
        config = Configuration(host=base_url, access_token=token)
        self.api_client = ApiClient(configuration=config)
        self.organizations_api = OrganizationsApi(self.api_client)

    def list(self, limit: int = 50, skip: int = 0) -> list[Organization]:
        """List organizations for the authenticated user.

        Args:
            limit: Maximum number of organizations to return (1-100, default: 50)
            skip: Number of organizations to skip for pagination (default: 0)

        Returns:
            List of Organization objects

        Raises:
            CodegenError: If the API request fails
        """
        try:
            response = self.organizations_api.get_organizations_v1_organizations_get(
                limit=min(limit, 100),  # API enforces max of 100
                skip=skip,
                authorization=f"Bearer {self.token}",
            )
            return [Organization(org) for org in response.items]
        except ApiException as e:
            error = handle_api_error(e.status, str(e), getattr(e, "body", None))
            raise error from e

    def list_all(self, page_size: int = 50) -> Iterator[Organization]:
        """Iterate through all organizations for the authenticated user.

        Args:
            page_size: Number of organizations to fetch per page (1-100, default: 50)

        Yields:
            Organization objects one by one

        Raises:
            CodegenError: If any API request fails
        """
        skip = 0
        page_size = min(page_size, 100)  # API enforces max of 100

        while True:
            organizations = self.list(limit=page_size, skip=skip)
            if not organizations:
                break

            yield from organizations

            # If we got fewer results than requested, we've reached the end
            if len(organizations) < page_size:
                break

            skip += page_size

    def get_page(self, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        """Get a specific page of organizations with pagination metadata.

        Args:
            page: Page number (1-based, default: 1)
            page_size: Number of organizations per page (1-100, default: 50)

        Returns:
            Dictionary containing:
            - items: List of Organization objects
            - total: Total number of organizations
            - page: Current page number
            - size: Page size
            - pages: Total number of pages

        Raises:
            CodegenError: If the API request fails
        """
        skip = (page - 1) * page_size
        page_size = min(page_size, 100)  # API enforces max of 100

        try:
            response = self.organizations_api.get_organizations_v1_organizations_get(limit=page_size, skip=skip, authorization=f"Bearer {self.token}")

            return {"items": [Organization(org) for org in response.items], "total": response.total, "page": response.page, "size": response.size, "pages": response.pages}
        except ApiException as e:
            error = handle_api_error(e.status, str(e), getattr(e, "body", None))
            raise error from e
