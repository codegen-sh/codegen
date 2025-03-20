"""Sentry API client for interacting with the Sentry API."""

import os
from typing import Any, Optional

import requests
from pydantic import BaseModel, Field


class SentryIssue(BaseModel):
    """Sentry issue model."""

    id: str = Field(..., description="Issue ID")
    shortId: str = Field(..., description="Short ID (e.g., PROJECT-123)")
    title: str = Field(..., description="Issue title")
    culprit: str = Field(..., description="Culprit")
    status: str = Field(..., description="Issue status")
    level: str = Field(..., description="Issue level (e.g., error, warning)")
    project: dict[str, Any] = Field(..., description="Project information")
    count: int = Field(..., description="Number of events")
    userCount: int = Field(..., description="Number of users affected")
    firstSeen: str = Field(..., description="First seen timestamp")
    lastSeen: str = Field(..., description="Last seen timestamp")
    permalink: str = Field(..., description="Permalink to the issue")


class SentryEvent(BaseModel):
    """Sentry event model."""

    id: str = Field(..., description="Event ID")
    eventID: str = Field(..., description="Event ID")
    title: str = Field(..., description="Event title")
    message: Optional[str] = Field(None, description="Event message")
    dateCreated: str = Field(..., description="Date created")
    user: Optional[dict[str, Any]] = Field(None, description="User information")
    tags: list[dict[str, str]] = Field(..., description="Event tags")
    entries: list[dict[str, Any]] = Field(..., description="Event entries")
    contexts: dict[str, Any] = Field(..., description="Event contexts")
    sdk: dict[str, Any] = Field(..., description="SDK information")
    metadata: dict[str, Any] = Field(..., description="Event metadata")


class SentryOrganization(BaseModel):
    """Sentry organization model."""

    id: str = Field(..., description="Organization ID")
    slug: str = Field(..., description="Organization slug")
    name: str = Field(..., description="Organization name")
    dateCreated: str = Field(..., description="Date created")
    isEarlyAdopter: bool = Field(..., description="Is early adopter")
    require2FA: bool = Field(..., description="Requires 2FA")
    status: dict[str, Any] = Field(..., description="Organization status")


class SentryProject(BaseModel):
    """Sentry project model."""

    id: str = Field(..., description="Project ID")
    slug: str = Field(..., description="Project slug")
    name: str = Field(..., description="Project name")
    platform: Optional[str] = Field(None, description="Project platform")
    dateCreated: str = Field(..., description="Date created")
    isBookmarked: bool = Field(..., description="Is bookmarked")
    isMember: bool = Field(..., description="Is member")
    features: list[str] = Field(..., description="Project features")
    firstEvent: Optional[str] = Field(None, description="First event timestamp")
    firstTransactionEvent: Optional[bool] = Field(None, description="Has first transaction event")
    access: list[str] = Field(..., description="Access levels")
    hasAccess: bool = Field(..., description="Has access")
    hasMinifiedStackTrace: bool = Field(..., description="Has minified stack trace")
    hasMonitors: bool = Field(..., description="Has monitors")
    hasProfiles: bool = Field(..., description="Has profiles")
    hasReplays: bool = Field(..., description="Has replays")
    hasSessions: bool = Field(..., description="Has sessions")
    isInternal: bool = Field(..., description="Is internal")
    isPublic: bool = Field(..., description="Is public")
    organization: dict[str, Any] = Field(..., description="Organization information")


class SentryClient:
    """Client for interacting with the Sentry API."""

    def __init__(self, auth_token: Optional[str] = None, installation_uuid: Optional[str] = None):
        """Initialize the Sentry API client.

        Args:
            auth_token: Sentry auth token. If not provided, will look for SENTRY_AUTH_TOKEN env var.
            installation_uuid: Sentry installation UUID. If not provided, will look for SENTRY_INSTALLATION_UUID env var.
        """
        self.auth_token = auth_token or os.environ.get("SENTRY_AUTH_TOKEN")
        self.installation_uuid = installation_uuid or os.environ.get("SENTRY_INSTALLATION_UUID")

        if not self.auth_token:
            msg = "Sentry auth token not provided. Set SENTRY_AUTH_TOKEN environment variable."
            raise ValueError(msg)

        self.base_url = "https://sentry.io/api/0"
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, params: Optional[dict[str, Any]] = None, data: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """Make a request to the Sentry API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint
            params: Query parameters
            data: Request body data

        Returns:
            Response data as a dictionary
        """
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, params=params, json=data)
        response.raise_for_status()
        return response.json()

    def get_organizations(self) -> list[SentryOrganization]:
        """Get a list of organizations the user has access to.

        Returns:
            List of organizations
        """
        data = self._make_request("GET", "/organizations/")
        return [SentryOrganization(**org) for org in data]

    def get_projects(self, organization_slug: str) -> list[SentryProject]:
        """Get a list of projects for an organization.

        Args:
            organization_slug: Organization slug

        Returns:
            List of projects
        """
        data = self._make_request("GET", f"/organizations/{organization_slug}/projects/")
        return [SentryProject(**project) for project in data]

    def get_issues(
        self,
        organization_slug: str,
        project_slug: Optional[str] = None,
        query: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get a list of issues for an organization or project.

        Args:
            organization_slug: Organization slug
            project_slug: Optional project slug to filter by
            query: Optional search query
            status: Optional status filter (e.g., "resolved", "unresolved")
            limit: Maximum number of issues to return
            cursor: Pagination cursor

        Returns:
            Dictionary containing issues and pagination info
        """
        params = {
            "limit": limit,
        }

        if project_slug:
            params["project"] = project_slug

        if query:
            params["query"] = query

        if status:
            params["status"] = status

        if cursor:
            params["cursor"] = cursor

        return self._make_request("GET", f"/organizations/{organization_slug}/issues/", params=params)

    def get_issue_details(self, issue_id: str, organization_slug: str) -> SentryIssue:
        """Get details for a specific issue.

        Args:
            issue_id: Issue ID
            organization_slug: Organization slug

        Returns:
            Issue details
        """
        data = self._make_request("GET", f"/organizations/{organization_slug}/issues/{issue_id}/")
        return SentryIssue(**data)

    def get_issue_events(
        self,
        issue_id: str,
        organization_slug: str,
        limit: int = 100,
        cursor: Optional[str] = None,
    ) -> dict[str, Any]:
        """Get events for a specific issue.

        Args:
            issue_id: Issue ID
            organization_slug: Organization slug
            limit: Maximum number of events to return
            cursor: Pagination cursor

        Returns:
            Dictionary containing events and pagination info
        """
        params = {
            "limit": limit,
        }

        if cursor:
            params["cursor"] = cursor

        return self._make_request("GET", f"/organizations/{organization_slug}/issues/{issue_id}/events/", params=params)

    def get_event_details(self, event_id: str, organization_slug: str, project_slug: str) -> SentryEvent:
        """Get details for a specific event.

        Args:
            event_id: Event ID
            organization_slug: Organization slug
            project_slug: Project slug

        Returns:
            Event details
        """
        data = self._make_request("GET", f"/projects/{organization_slug}/{project_slug}/events/{event_id}/")
        return SentryEvent(**data)
