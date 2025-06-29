"""Users API client for the Codegen SDK."""

from collections.abc import Iterator
from typing import Any

from codegen_api_client.api.users_api import UsersApi
from codegen_api_client.api_client import ApiClient
from codegen_api_client.configuration import Configuration
from codegen_api_client.models.user_response import UserResponse
from codegen_api_client.rest import ApiException

from codegen.agents.constants import CODEGEN_BASE_API_URL
from codegen.exceptions import handle_api_error


class User:
    """Represents a user with convenient access to their properties."""

    def __init__(self, data: UserResponse):
        self._data = data

    @property
    def id(self) -> int:
        """User ID."""
        return self._data.id

    @property
    def email(self) -> str | None:
        """User email address."""
        return self._data.email

    @property
    def github_user_id(self) -> str:
        """GitHub user ID."""
        return self._data.github_user_id

    @property
    def github_username(self) -> str:
        """GitHub username."""
        return self._data.github_username

    @property
    def avatar_url(self) -> str | None:
        """User avatar URL."""
        return self._data.avatar_url

    @property
    def full_name(self) -> str | None:
        """User's full name."""
        return self._data.full_name

    def to_dict(self) -> dict[str, Any]:
        """Convert user to dictionary."""
        return self._data.to_dict()

    def __repr__(self) -> str:
        return f"User(id={self.id}, github_username='{self.github_username}', email='{self.email}')"


class Users:
    """API client for managing users in Codegen."""

    def __init__(self, token: str | None, org_id: int | str, base_url: str = CODEGEN_BASE_API_URL):
        """Initialize the Users client.

        Args:
            token: API authentication token
            org_id: Organization ID to scope user operations to
            base_url: Base URL for the API (defaults to production)
        """
        self.token = token
        self.org_id = str(org_id)

        # Configure API client
        config = Configuration(host=base_url, access_token=token)
        self.api_client = ApiClient(configuration=config)
        self.users_api = UsersApi(self.api_client)

    def list(self, limit: int = 50, skip: int = 0) -> list[User]:
        """List users in the organization.

        Args:
            limit: Maximum number of users to return (1-100, default: 50)
            skip: Number of users to skip for pagination (default: 0)

        Returns:
            List of User objects

        Raises:
            CodegenError: If the API request fails
        """
        try:
            response = self.users_api.get_users_v1_organizations_org_id_users_get(
                org_id=self.org_id,
                limit=min(limit, 100),  # API enforces max of 100
                skip=skip,
                authorization=f"Bearer {self.token}",
            )
            return [User(user) for user in response.items]
        except ApiException as e:
            error = handle_api_error(e.status, str(e), getattr(e, "body", None))
            raise error from e

    def list_all(self, page_size: int = 50) -> Iterator[User]:
        """Iterate through all users in the organization.

        Args:
            page_size: Number of users to fetch per page (1-100, default: 50)

        Yields:
            User objects one by one

        Raises:
            CodegenError: If any API request fails
        """
        skip = 0
        page_size = min(page_size, 100)  # API enforces max of 100

        while True:
            users = self.list(limit=page_size, skip=skip)
            if not users:
                break

            yield from users

            # If we got fewer results than requested, we've reached the end
            if len(users) < page_size:
                break

            skip += page_size

    def get(self, user_id: int | str) -> User:
        """Get a specific user by ID.

        Args:
            user_id: User ID to retrieve

        Returns:
            User object

        Raises:
            CodegenError: If the API request fails or user is not found
        """
        try:
            response = self.users_api.get_user_v1_organizations_org_id_users_user_id_get(org_id=self.org_id, user_id=str(user_id), authorization=f"Bearer {self.token}")
            return User(response)
        except ApiException as e:
            error = handle_api_error(e.status, str(e), getattr(e, "body", None))
            raise error from e

    def get_page(self, page: int = 1, page_size: int = 50) -> dict[str, Any]:
        """Get a specific page of users with pagination metadata.

        Args:
            page: Page number (1-based, default: 1)
            page_size: Number of users per page (1-100, default: 50)

        Returns:
            Dictionary containing:
            - items: List of User objects
            - total: Total number of users
            - page: Current page number
            - size: Page size
            - pages: Total number of pages

        Raises:
            CodegenError: If the API request fails
        """
        skip = (page - 1) * page_size
        page_size = min(page_size, 100)  # API enforces max of 100

        try:
            response = self.users_api.get_users_v1_organizations_org_id_users_get(org_id=self.org_id, limit=page_size, skip=skip, authorization=f"Bearer {self.token}")

            return {"items": [User(user) for user in response.items], "total": response.total, "page": response.page, "size": response.size, "pages": response.pages}
        except ApiException as e:
            error = handle_api_error(e.status, str(e), getattr(e, "body", None))
            raise error from e

    def find_by_github_username(self, github_username: str) -> User | None:
        """Find a user by their GitHub username.

        Args:
            github_username: GitHub username to search for

        Returns:
            User object if found, None otherwise

        Raises:
            CodegenError: If the API request fails
        """
        # Since the API doesn't support filtering by username, we need to iterate
        for user in self.list_all():
            if user.github_username == github_username:
                return user
        return None

    def find_by_email(self, email: str) -> User | None:
        """Find a user by their email address.

        Args:
            email: Email address to search for

        Returns:
            User object if found, None otherwise

        Raises:
            CodegenError: If the API request fails
        """
        # Since the API doesn't support filtering by email, we need to iterate
        for user in self.list_all():
            if user.email == email:
                return user
        return None
