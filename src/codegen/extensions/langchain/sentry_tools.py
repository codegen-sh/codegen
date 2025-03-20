"""LangChain tools for Sentry integration."""

from typing import ClassVar, Optional

from langchain_core.tools.base import BaseTool
from pydantic import BaseModel, Field

from codegen.extensions.sentry.config import DEFAULT_ORGANIZATION_SLUG
from codegen.extensions.tools.sentry.tools import (
    view_sentry_event_details,
    view_sentry_issue_details,
    view_sentry_issues,
)
from codegen.sdk.core.codebase import Codebase


class ViewSentryIssuesInput(BaseModel):
    """Input for viewing Sentry issues."""

    organization_slug: str = Field(
        default=DEFAULT_ORGANIZATION_SLUG,
        description="Organization slug (e.g., 'codegen-sh', 'ramp')",
    )
    project_slug: Optional[str] = Field(
        default=None,
        description="Optional project slug to filter by (e.g., 'codegen', 'api')",
    )
    query: Optional[str] = Field(
        default=None,
        description="Optional search query to filter issues",
    )
    status: str = Field(
        default="unresolved",
        description="Status filter (e.g., 'resolved', 'unresolved', 'ignored')",
    )
    limit: int = Field(
        default=20,
        description="Maximum number of issues to return",
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Pagination cursor for fetching the next page of results",
    )


class ViewSentryIssueDetailsInput(BaseModel):
    """Input for viewing a specific Sentry issue."""

    issue_id: str = Field(
        ...,
        description="ID of the issue to view",
    )
    organization_slug: str = Field(
        default=DEFAULT_ORGANIZATION_SLUG,
        description="Organization slug (e.g., 'codegen-sh', 'ramp')",
    )
    limit: int = Field(
        default=10,
        description="Maximum number of events to return",
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Pagination cursor for fetching the next page of events",
    )


class ViewSentryEventDetailsInput(BaseModel):
    """Input for viewing a specific Sentry event."""

    event_id: str = Field(
        ...,
        description="ID of the event to view",
    )
    organization_slug: str = Field(
        default=DEFAULT_ORGANIZATION_SLUG,
        description="Organization slug (e.g., 'codegen-sh', 'ramp')",
    )
    project_slug: str = Field(
        default="codegen",
        description="Project slug (e.g., 'codegen', 'api')",
    )


class ViewSentryIssuesTool(BaseTool):
    """Tool for viewing Sentry issues."""

    name: ClassVar[str] = "view_sentry_issues"
    description: ClassVar[str] = """
    View a list of Sentry issues for an organization or project.

    This tool allows you to retrieve and filter Sentry issues by organization, project, status, and search query.
    Results are paginated, and you can use the cursor parameter to fetch additional pages.
    """
    args_schema: ClassVar[type[BaseModel]] = ViewSentryIssuesInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        organization_slug: str = DEFAULT_ORGANIZATION_SLUG,
        project_slug: Optional[str] = None,
        query: Optional[str] = None,
        status: str = "unresolved",
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> str:
        result = view_sentry_issues(
            codebase=self.codebase,
            organization_slug=organization_slug,
            project_slug=project_slug,
            query=query,
            status=status,
            limit=limit,
            cursor=cursor,
        )
        return result.render()


class ViewSentryIssueDetailsTool(BaseTool):
    """Tool for viewing details of a specific Sentry issue."""

    name: ClassVar[str] = "view_sentry_issue"
    description: ClassVar[str] = """
    View detailed information about a specific Sentry issue, including its events.

    This tool retrieves comprehensive information about a Sentry issue, including its metadata and associated events.
    Events are paginated, and you can use the cursor parameter to fetch additional pages.
    """
    args_schema: ClassVar[type[BaseModel]] = ViewSentryIssueDetailsInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        issue_id: str,
        organization_slug: str = DEFAULT_ORGANIZATION_SLUG,
        limit: int = 10,
        cursor: Optional[str] = None,
    ) -> str:
        result = view_sentry_issue_details(
            codebase=self.codebase,
            issue_id=issue_id,
            organization_slug=organization_slug,
            limit=limit,
            cursor=cursor,
        )
        return result.render()


class ViewSentryEventDetailsTool(BaseTool):
    """Tool for viewing details of a specific Sentry event."""

    name: ClassVar[str] = "view_sentry_event"
    description: ClassVar[str] = """
    View detailed information about a specific Sentry event.

    This tool retrieves comprehensive information about a Sentry event, including its metadata, tags, user information,
    and stack trace (if available).
    """
    args_schema: ClassVar[type[BaseModel]] = ViewSentryEventDetailsInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        event_id: str,
        organization_slug: str = DEFAULT_ORGANIZATION_SLUG,
        project_slug: str = "codegen",
    ) -> str:
        result = view_sentry_event_details(
            codebase=self.codebase,
            event_id=event_id,
            organization_slug=organization_slug,
            project_slug=project_slug,
        )
        return result.render()


class ViewSentryToolInput(BaseModel):
    """Input for the combined ViewSentryTool."""

    action: str = Field(
        default="view_issues",
        description="Action to perform: 'view_issues', 'view_issue', or 'view_event'",
    )
    organization_slug: str = Field(
        default=DEFAULT_ORGANIZATION_SLUG,
        description="Organization slug (e.g., 'codegen-sh', 'ramp')",
    )
    project_slug: Optional[str] = Field(
        default=None,
        description="Project slug (e.g., 'codegen', 'api'). Required for 'view_event' action.",
    )
    issue_id: Optional[str] = Field(
        default=None,
        description="ID of the issue to view. Required for 'view_issue' action.",
    )
    event_id: Optional[str] = Field(
        default=None,
        description="ID of the event to view. Required for 'view_event' action.",
    )
    query: Optional[str] = Field(
        default=None,
        description="Search query for filtering issues. Only used with 'view_issues' action.",
    )
    status: str = Field(
        default="unresolved",
        description="Status filter for issues (e.g., 'resolved', 'unresolved'). Only used with 'view_issues' action.",
    )
    limit: int = Field(
        default=20,
        description="Maximum number of results to return. Used with 'view_issues' and 'view_issue' actions.",
    )
    cursor: Optional[str] = Field(
        default=None,
        description="Pagination cursor for fetching the next page of results. Used with 'view_issues' and 'view_issue' actions.",
    )


class ViewSentryTool(BaseTool):
    """Combined tool for viewing Sentry issues and events."""

    name: ClassVar[str] = "view_sentry"
    description: ClassVar[str] = """
    View Sentry issues and events.

    This tool allows you to:
    1. View a list of Sentry issues for an organization or project
    2. View details of a specific Sentry issue, including its events
    3. View details of a specific Sentry event, including stack traces

    Specify the action parameter to choose which operation to perform:
    - 'view_issues': List issues (default)
    - 'view_issue': View a specific issue (requires issue_id)
    - 'view_event': View a specific event (requires event_id and project_slug)
    """
    args_schema: ClassVar[type[BaseModel]] = ViewSentryToolInput
    codebase: Codebase = Field(exclude=True)

    def __init__(self, codebase: Codebase) -> None:
        super().__init__(codebase=codebase)

    def _run(
        self,
        action: str = "view_issues",
        organization_slug: str = DEFAULT_ORGANIZATION_SLUG,
        project_slug: Optional[str] = None,
        issue_id: Optional[str] = None,
        event_id: Optional[str] = None,
        query: Optional[str] = None,
        status: str = "unresolved",
        limit: int = 20,
        cursor: Optional[str] = None,
    ) -> str:
        if action == "view_issues":
            result = view_sentry_issues(
                codebase=self.codebase,
                organization_slug=organization_slug,
                project_slug=project_slug,
                query=query,
                status=status,
                limit=limit,
                cursor=cursor,
            )
        elif action == "view_issue":
            if not issue_id:
                return "Error: Missing required parameter 'issue_id' for action 'view_issue'"

            result = view_sentry_issue_details(
                codebase=self.codebase,
                issue_id=issue_id,
                organization_slug=organization_slug,
                limit=limit,
                cursor=cursor,
            )
        elif action == "view_event":
            if not event_id:
                return "Error: Missing required parameter 'event_id' for action 'view_event'"

            if not project_slug:
                return "Error: Missing required parameter 'project_slug' for action 'view_event'"

            result = view_sentry_event_details(
                codebase=self.codebase,
                event_id=event_id,
                organization_slug=organization_slug,
                project_slug=project_slug,
            )
        else:
            return f"Error: Unknown action '{action}'. Supported actions: 'view_issues', 'view_issue', 'view_event'"

        return result.render()


def get_sentry_tools(codebase: Codebase) -> list[BaseTool]:
    """Get all Sentry tools initialized with a codebase.

    Args:
        codebase: The codebase to operate on

    Returns:
        List of initialized Sentry tools
    """
    return [
        ViewSentryIssuesTool(codebase),
        ViewSentryIssueDetailsTool(codebase),
        ViewSentryEventDetailsTool(codebase),
        ViewSentryTool(codebase),
    ]
