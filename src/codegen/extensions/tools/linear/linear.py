"""Tools for interacting with Linear."""

from typing import ClassVar

from pydantic import Field

from codegen.extensions.linear.linear_client import LinearClient

from ..observation import Observation


class LinearIssueObservation(Observation):
    """Response from getting a Linear issue."""

    issue_id: str = Field(description="ID of the issue")
    issue_data: dict = Field(description="Full issue data")

    str_template: ClassVar[str] = "Issue {issue_id}"


class LinearCommentsObservation(Observation):
    """Response from getting Linear issue comments."""

    issue_id: str = Field(description="ID of the issue")
    comments: list[dict] = Field(description="List of comments")

    str_template: ClassVar[str] = "{comment_count} comments on issue {issue_id}"

    def _get_details(self) -> dict[str, int]:
        """Get details for string representation."""
        return {"comment_count": len(self.comments)}


class LinearCommentObservation(Observation):
    """Response from commenting on a Linear issue."""

    issue_id: str = Field(description="ID of the issue")
    comment: dict = Field(description="Created comment data")

    str_template: ClassVar[str] = "Added comment to issue {issue_id}"


class LinearWebhookObservation(Observation):
    """Response from registering a Linear webhook."""

    webhook_url: str = Field(description="URL of the registered webhook")
    team_id: str = Field(description="ID of the team")
    response: dict = Field(description="Full webhook registration response")

    str_template: ClassVar[str] = "Registered webhook for team {team_id}"


class LinearSearchObservation(Observation):
    """Response from searching Linear issues."""

    query: str = Field(description="Search query used")
    issues: list[dict] = Field(description="List of matching issues")

    str_template: ClassVar[str] = "Found {issue_count} issues matching '{query}'"

    def _get_details(self) -> dict[str, str | int]:
        """Get details for string representation."""
        return {
            "issue_count": len(self.issues),
            "query": self.query,
        }


class LinearCreateIssueObservation(Observation):
    """Response from creating a Linear issue."""

    title: str = Field(description="Title of the created issue")
    team_id: str | None = Field(description="Team ID if specified")
    issue_data: dict = Field(description="Created issue data")

    str_template: ClassVar[str] = "Created issue '{title}'"


class LinearTeamsObservation(Observation):
    """Response from getting Linear teams."""

    teams: list[dict] = Field(description="List of teams")

    str_template: ClassVar[str] = "Found {team_count} teams"

    def _get_details(self) -> dict[str, int]:
        """Get details for string representation."""
        return {"team_count": len(self.teams)}


def linear_get_issue_tool(client: LinearClient, issue_id: str) -> LinearIssueObservation:
    """Get an issue by its ID."""
    try:
        issue = client.get_issue(issue_id)
        return LinearIssueObservation(
            status="success",
            issue_id=issue_id,
            issue_data=issue.dict(),
        )
    except Exception as e:
        return LinearIssueObservation(
            status="error",
            error=f"Failed to get issue: {e!s}",
            issue_id=issue_id,
            issue_data={},
        )


def linear_get_issue_comments_tool(client: LinearClient, issue_id: str) -> LinearCommentsObservation:
    """Get comments for a specific issue."""
    try:
        comments = client.get_issue_comments(issue_id)
        return LinearCommentsObservation(
            status="success",
            issue_id=issue_id,
            comments=[comment.dict() for comment in comments],
        )
    except Exception as e:
        return LinearCommentsObservation(
            status="error",
            error=f"Failed to get issue comments: {e!s}",
            issue_id=issue_id,
            comments=[],
        )


def linear_comment_on_issue_tool(client: LinearClient, issue_id: str, body: str) -> LinearCommentObservation:
    """Add a comment to an issue."""
    try:
        comment = client.comment_on_issue(issue_id, body)
        return LinearCommentObservation(
            status="success",
            issue_id=issue_id,
            comment=comment,
        )
    except Exception as e:
        return LinearCommentObservation(
            status="error",
            error=f"Failed to comment on issue: {e!s}",
            issue_id=issue_id,
            comment={},
        )


def linear_register_webhook_tool(
    client: LinearClient,
    webhook_url: str,
    team_id: str,
    secret: str,
    enabled: bool,
    resource_types: list[str],
) -> LinearWebhookObservation:
    """Register a webhook with Linear."""
    try:
        response = client.register_webhook(webhook_url, team_id, secret, enabled, resource_types)
        return LinearWebhookObservation(
            status="success",
            webhook_url=webhook_url,
            team_id=team_id,
            response=response,
        )
    except Exception as e:
        return LinearWebhookObservation(
            status="error",
            error=f"Failed to register webhook: {e!s}",
            webhook_url=webhook_url,
            team_id=team_id,
            response={},
        )


def linear_search_issues_tool(client: LinearClient, query: str, limit: int = 10) -> LinearSearchObservation:
    """Search for issues using a query string."""
    try:
        issues = client.search_issues(query, limit)
        return LinearSearchObservation(
            status="success",
            query=query,
            issues=[issue.dict() for issue in issues],
        )
    except Exception as e:
        return LinearSearchObservation(
            status="error",
            error=f"Failed to search issues: {e!s}",
            query=query,
            issues=[],
        )


def linear_create_issue_tool(client: LinearClient, title: str, description: str | None = None, team_id: str | None = None) -> LinearCreateIssueObservation:
    """Create a new issue."""
    try:
        issue = client.create_issue(title, description, team_id)
        return LinearCreateIssueObservation(
            status="success",
            title=title,
            team_id=team_id,
            issue_data=issue.dict(),
        )
    except Exception as e:
        return LinearCreateIssueObservation(
            status="error",
            error=f"Failed to create issue: {e!s}",
            title=title,
            team_id=team_id,
            issue_data={},
        )


def linear_get_teams_tool(client: LinearClient) -> LinearTeamsObservation:
    """Get all teams the authenticated user has access to."""
    try:
        teams = client.get_teams()
        return LinearTeamsObservation(
            status="success",
            teams=[team.dict() for team in teams],
        )
    except Exception as e:
        return LinearTeamsObservation(
            status="error",
            error=f"Failed to get teams: {e!s}",
            teams=[],
        )
