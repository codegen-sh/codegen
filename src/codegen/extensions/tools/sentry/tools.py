"""Tools for interacting with Sentry."""

from typing import Any, ClassVar, Dict, List, Optional

from pydantic import Field

from codegen.extensions.sentry.config import (
    DEFAULT_ORGANIZATION_SLUG,
    get_available_organizations,
    get_installation_uuid,
    get_sentry_auth_token,
)
from codegen.extensions.sentry.sentry_client import SentryClient
from codegen.sdk.core.codebase import Codebase

from ..observation import Observation


class SentryIssuesObservation(Observation):
    """Response from viewing Sentry issues."""

    organization_slug: str = Field(description="Organization slug")
    project_slug: Optional[str] = Field(None, description="Project slug (if specified)")
    query: Optional[str] = Field(None, description="Search query (if specified)")
    status: str = Field(description="Status filter (if specified)")
    issues: List[Dict[str, Any]] = Field(description="List of issues")
    has_more: bool = Field(description="Whether there are more issues to fetch")
    next_cursor: Optional[str] = Field(None, description="Cursor for fetching the next page")

    str_template: ClassVar[str] = "Found {issue_count} issues in {organization_slug}"

    def _get_details(self) -> Dict[str, Any]:
        """Get details for string representation."""
        return {
            "issue_count": len(self.issues),
            "organization_slug": self.organization_slug,
        }

    def render(self) -> str:
        """Render the issues view."""
        header = f"[SENTRY ISSUES]: Organization: {self.organization_slug}"

        if self.project_slug:
            header += f", Project: {self.project_slug}"

        if self.query:
            header += f", Query: '{self.query}'"

        if self.status:
            header += f", Status: {self.status}"

        header += f"\nFound {len(self.issues)} issues"

        if self.has_more:
            header += " (more available)"

        if not self.issues:
            return f"{header}\n\nNo issues found."

        issues_text = ""
        for issue in self.issues:
            issues_text += f"\n\n## {issue.get('shortId', 'Unknown')} - {issue.get('title', 'Untitled')}"
            issues_text += f"\nStatus: {issue.get('status', 'Unknown')}"
            issues_text += f"\nLevel: {issue.get('level', 'Unknown')}"
            issues_text += f"\nEvents: {issue.get('count', 0)}"
            issues_text += f"\nUsers affected: {issue.get('userCount', 0)}"
            issues_text += f"\nFirst seen: {issue.get('firstSeen', 'Unknown')}"
            issues_text += f"\nLast seen: {issue.get('lastSeen', 'Unknown')}"
            issues_text += f"\nPermalink: {issue.get('permalink', 'Unknown')}"

        return f"{header}{issues_text}"


class SentryIssueDetailsObservation(Observation):
    """Response from viewing a specific Sentry issue."""

    organization_slug: str = Field(description="Organization slug")
    issue_id: str = Field(description="Issue ID")
    issue_data: Dict[str, Any] = Field(description="Issue data")
    events: List[Dict[str, Any]] = Field(description="List of events for this issue")
    has_more_events: bool = Field(description="Whether there are more events to fetch")
    next_cursor: Optional[str] = Field(None, description="Cursor for fetching the next page of events")

    str_template: ClassVar[str] = "Issue {issue_id} with {event_count} events"

    def _get_details(self) -> Dict[str, Any]:
        """Get details for string representation."""
        return {
            "issue_id": self.issue_id,
            "event_count": len(self.events),
        }

    def render(self) -> str:
        """Render the issue details view."""
        issue = self.issue_data

        header = f"[SENTRY ISSUE]: {issue.get('shortId', 'Unknown')} - {issue.get('title', 'Untitled')}"
        header += f"\nOrganization: {self.organization_slug}"

        details = f"\nStatus: {issue.get('status', 'Unknown')}"
        details += f"\nLevel: {issue.get('level', 'Unknown')}"
        details += f"\nEvents: {issue.get('count', 0)}"
        details += f"\nUsers affected: {issue.get('userCount', 0)}"
        details += f"\nFirst seen: {issue.get('firstSeen', 'Unknown')}"
        details += f"\nLast seen: {issue.get('lastSeen', 'Unknown')}"
        details += f"\nPermalink: {issue.get('permalink', 'Unknown')}"

        events_header = f"\n\n## Events ({len(self.events)})"
        if self.has_more_events:
            events_header += " (more available)"

        events_text = ""
        for event in self.events:
            events_text += f"\n\n### Event {event.get('eventID', 'Unknown')}"
            events_text += f"\nTimestamp: {event.get('dateCreated', 'Unknown')}"

            # Add user info if available
            user = event.get('user')
            if user:
                events_text += f"\nUser: {user.get('username') or user.get('email') or user.get('ip_address') or 'Anonymous'}"

            # Add tags
            tags = event.get('tags', [])
            if tags:
                events_text += "\nTags:"
                for tag in tags:
                    events_text += f"\n  - {tag.get('key', '')}: {tag.get('value', '')}"

        return f"{header}{details}{events_header}{events_text}"


class SentryEventDetailsObservation(Observation):
    """Response from viewing a specific Sentry event."""

    organization_slug: str = Field(description="Organization slug")
    project_slug: str = Field(description="Project slug")
    event_id: str = Field(description="Event ID")
    event_data: Dict[str, Any] = Field(description="Event data")

    str_template: ClassVar[str] = "Event {event_id}"

    def render(self) -> str:
        """Render the event details view."""
        event = self.event_data

        header = f"[SENTRY EVENT]: {event.get('eventID', 'Unknown')}"
        header += f"\nOrganization: {self.organization_slug}"
        header += f"\nProject: {self.project_slug}"
        header += f"\nTitle: {event.get('title', 'Untitled')}"

        details = f"\nTimestamp: {event.get('dateCreated', 'Unknown')}"

        # Add user info if available
        user = event.get('user')
        if user:
            details += f"\nUser: {user.get('username') or user.get('email') or user.get('ip_address') or 'Anonymous'}"

        # Add tags
        tags = event.get('tags', [])
        if tags:
            details += "\nTags:"
            for tag in tags:
                details += f"\n  - {tag.get('key', '')}: {tag.get('value', '')}"

        # Add exception info if available
        exception_entries = [entry for entry in event.get('entries', []) if entry.get('type') == 'exception']
        if exception_entries:
            details += "\n\n## Exception"
            for entry in exception_entries:
                for exception in entry.get('data', {}).get('values', []):
                    details += f"\n\n### {exception.get('type', 'Unknown')}: {exception.get('value', 'Unknown')}"

                    # Add stack trace
                    frames = exception.get('stacktrace', {}).get('frames', [])
                    if frames:
                        details += "\n\nStack Trace:"
                        for frame in frames:
                            filename = frame.get('filename', frame.get('abs_path', 'Unknown'))
                            function = frame.get('function', 'Unknown')
                            lineno = frame.get('lineno', '?')
                            details += f"\n  - {filename}:{lineno} in {function}"

                            # Add context if available
                            context_line = frame.get('context_line')
                            if context_line:
                                details += f"\n    {context_line.strip()}"

        return f"{header}{details}"


def view_sentry_issues(
    codebase: Codebase,
    organization_slug: str = DEFAULT_ORGANIZATION_SLUG,
    project_slug: Optional[str] = None,
    query: Optional[str] = None,
    status: str = "unresolved",
    limit: int = 20,
    cursor: Optional[str] = None,
) -> SentryIssuesObservation:
    """View Sentry issues for an organization or project.

    Args:
        codebase: The codebase to operate on
        organization_slug: Organization slug
        project_slug: Optional project slug to filter by
        query: Optional search query
        status: Status filter (e.g., "resolved", "unresolved")
        limit: Maximum number of issues to return
        cursor: Pagination cursor
    """
    try:
        # Get auth token and installation UUID
        auth_token = get_sentry_auth_token()
        installation_uuid = get_installation_uuid(organization_slug)

        if not auth_token:
            return SentryIssuesObservation(
                status="error",
                error="Sentry auth token not found. Please set the SENTRY_AUTH_TOKEN environment variable.",
                organization_slug=organization_slug,
                project_slug=project_slug,
                query=query,
                status=status,
                issues=[],
                has_more=False,
            )

        if not installation_uuid:
            available_orgs = get_available_organizations()
            if not available_orgs:
                org_message = "No Sentry organizations configured. Please set the SENTRY_CODEGEN_INSTALLATION_UUID or SENTRY_RAMP_INSTALLATION_UUID environment variables."
            else:
                org_message = f"Available organizations: {', '.join(available_orgs.keys())}"

            return SentryIssuesObservation(
                status="error",
                error=f"Sentry installation UUID not found for organization '{organization_slug}'. {org_message}",
                organization_slug=organization_slug,
                project_slug=project_slug,
                query=query,
                status=status,
                issues=[],
                has_more=False,
            )

        # Initialize Sentry client
        client = SentryClient(auth_token=auth_token, installation_uuid=installation_uuid)

        # Get issues
        response = client.get_issues(
            organization_slug=organization_slug,
            project_slug=project_slug,
            query=query,
            status=status,
            limit=limit,
            cursor=cursor,
        )

        # Extract pagination info
        has_more = False
        next_cursor = None

        if isinstance(response, dict):
            issues = response.get('data', [])

            # Check for pagination info
            pagination = response.get('pagination', {})
            has_more = pagination.get('hasMore', False)
            next_cursor = pagination.get('nextCursor')
        else:
            issues = response

        return SentryIssuesObservation(
            status="success",
            organization_slug=organization_slug,
            project_slug=project_slug,
            query=query,
            status=status,
            issues=issues,
            has_more=has_more,
            next_cursor=next_cursor,
        )

    except Exception as e:
        return SentryIssuesObservation(
            status="error",
            error=f"Failed to view Sentry issues: {e!s}",
            organization_slug=organization_slug,
            project_slug=project_slug,
            query=query,
            status=status,
            issues=[],
            has_more=False,
        )


def view_sentry_issue_details(
    codebase: Codebase,
    issue_id: str,
    organization_slug: str = DEFAULT_ORGANIZATION_SLUG,
    limit: int = 10,
    cursor: Optional[str] = None,
) -> SentryIssueDetailsObservation:
    """View details for a specific Sentry issue.

    Args:
        codebase: The codebase to operate on
        issue_id: Issue ID
        organization_slug: Organization slug
        limit: Maximum number of events to return
        cursor: Pagination cursor
    """
    try:
        # Get auth token and installation UUID
        auth_token = get_sentry_auth_token()
        installation_uuid = get_installation_uuid(organization_slug)

        if not auth_token:
            return SentryIssueDetailsObservation(
                status="error",
                error="Sentry auth token not found. Please set the SENTRY_AUTH_TOKEN environment variable.",
                organization_slug=organization_slug,
                issue_id=issue_id,
                issue_data={},
                events=[],
                has_more_events=False,
            )

        if not installation_uuid:
            available_orgs = get_available_organizations()
            if not available_orgs:
                org_message = "No Sentry organizations configured. Please set the SENTRY_CODEGEN_INSTALLATION_UUID or SENTRY_RAMP_INSTALLATION_UUID environment variables."
            else:
                org_message = f"Available organizations: {', '.join(available_orgs.keys())}"

            return SentryIssueDetailsObservation(
                status="error",
                error=f"Sentry installation UUID not found for organization '{organization_slug}'. {org_message}",
                organization_slug=organization_slug,
                issue_id=issue_id,
                issue_data={},
                events=[],
                has_more_events=False,
            )

        # Initialize Sentry client
        client = SentryClient(auth_token=auth_token, installation_uuid=installation_uuid)

        # Get issue details
        issue = client.get_issue_details(issue_id=issue_id, organization_slug=organization_slug)

        # Get events for the issue
        events_response = client.get_issue_events(
            issue_id=issue_id,
            organization_slug=organization_slug,
            limit=limit,
            cursor=cursor,
        )

        # Extract pagination info
        has_more = False
        next_cursor = None

        if isinstance(events_response, dict):
            events = events_response.get('data', [])

            # Check for pagination info
            pagination = events_response.get('pagination', {})
            has_more = pagination.get('hasMore', False)
            next_cursor = pagination.get('nextCursor')
        else:
            events = events_response

        return SentryIssueDetailsObservation(
            status="success",
            organization_slug=organization_slug,
            issue_id=issue_id,
            issue_data=issue.dict() if hasattr(issue, 'dict') else issue,
            events=events,
            has_more_events=has_more,
            next_cursor=next_cursor,
        )

    except Exception as e:
        return SentryIssueDetailsObservation(
            status="error",
            error=f"Failed to view Sentry issue details: {e!s}",
            organization_slug=organization_slug,
            issue_id=issue_id,
            issue_data={},
            events=[],
            has_more_events=False,
        )


def view_sentry_event_details(
    codebase: Codebase,
    event_id: str,
    organization_slug: str = DEFAULT_ORGANIZATION_SLUG,
    project_slug: str = "codegen",
) -> SentryEventDetailsObservation:
    """View details for a specific Sentry event.

    Args:
        codebase: The codebase to operate on
        event_id: Event ID
        organization_slug: Organization slug
        project_slug: Project slug
    """
    try:
        # Get auth token and installation UUID
        auth_token = get_sentry_auth_token()
        installation_uuid = get_installation_uuid(organization_slug)

        if not auth_token:
            return SentryEventDetailsObservation(
                status="error",
                error="Sentry auth token not found. Please set the SENTRY_AUTH_TOKEN environment variable.",
                organization_slug=organization_slug,
                project_slug=project_slug,
                event_id=event_id,
                event_data={},
            )

        if not installation_uuid:
            available_orgs = get_available_organizations()
            if not available_orgs:
                org_message = "No Sentry organizations configured. Please set the SENTRY_CODEGEN_INSTALLATION_UUID or SENTRY_RAMP_INSTALLATION_UUID environment variables."
            else:
                org_message = f"Available organizations: {', '.join(available_orgs.keys())}"

            return SentryEventDetailsObservation(
                status="error",
                error=f"Sentry installation UUID not found for organization '{organization_slug}'. {org_message}",
                organization_slug=organization_slug,
                project_slug=project_slug,
                event_id=event_id,
                event_data={},
            )

        # Initialize Sentry client
        client = SentryClient(auth_token=auth_token, installation_uuid=installation_uuid)

        # Get event details
        event = client.get_event_details(
            event_id=event_id,
            organization_slug=organization_slug,
            project_slug=project_slug,
        )

        return SentryEventDetailsObservation(
            status="success",
            organization_slug=organization_slug,
            project_slug=project_slug,
            event_id=event_id,
            event_data=event.dict() if hasattr(event, 'dict') else event,
        )

    except Exception as e:
        return SentryEventDetailsObservation(
            status="error",
            error=f"Failed to view Sentry event details: {e!s}",
            organization_slug=organization_slug,
            project_slug=project_slug,
            event_id=event_id,
            event_data={},
        )
