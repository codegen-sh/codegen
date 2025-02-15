from typing import Any

from codegen.extensions.linear.linear_client import LinearClient


def linear_get_issue_tool(client: LinearClient, issue_id: str) -> dict[str, Any]:
    """Get an issue by its ID."""
    try:
        issue = client.get_issue(issue_id)
        return {"status": "success", "issue": issue.dict()}
    except Exception as e:
        return {"error": f"Failed to get issue: {e!s}"}


def linear_get_issue_comments_tool(client: LinearClient, issue_id: str) -> dict[str, Any]:
    """Get comments for a specific issue."""
    try:
        comments = client.get_issue_comments(issue_id)
        return {"status": "success", "comments": [comment.dict() for comment in comments]}
    except Exception as e:
        return {"error": f"Failed to get issue comments: {e!s}"}


def linear_comment_on_issue_tool(client: LinearClient, issue_id: str, body: str) -> dict[str, Any]:
    """Add a comment to an issue."""
    try:
        comment = client.comment_on_issue(issue_id, body)
        return {"status": "success", "comment": comment}
    except Exception as e:
        return {"error": f"Failed to comment on issue: {e!s}"}


def linear_register_webhook_tool(client: LinearClient, webhook_url: str, team_id: str, secret: str, enabled: bool, resource_types: list[str]) -> dict[str, Any]:
    """Register a webhook with Linear."""
    try:
        response = client.register_webhook(webhook_url, team_id, secret, enabled, resource_types)
        return {"status": "success", "response": response}
    except Exception as e:
        return {"error": f"Failed to register webhook: {e!s}"}


def linear_search_issues_tool(client: LinearClient, query: str, limit: int = 10) -> dict[str, Any]:
    """Search for issues using a query string."""
    try:
        issues = client.search_issues(query, limit)
        return {"status": "success", "issues": [issue.dict() for issue in issues]}
    except Exception as e:
        return {"error": f"Failed to search issues: {e!s}"}


def linear_create_issue_tool(client: LinearClient, title: str, description: str | None = None, team_id: str | None = None) -> dict[str, Any]:
    """Create a new issue."""
    try:
        issue = client.create_issue(title, description, team_id)
        return {"status": "success", "issue": issue.dict()}
    except Exception as e:
        return {"error": f"Failed to create issue: {e!s}"}


def linear_get_teams_tool(client: LinearClient) -> dict[str, Any]:
    """Get all teams the authenticated user has access to."""
    try:
        teams = client.get_teams()
        return {"status": "success", "teams": [team.dict() for team in teams]}
    except Exception as e:
        return {"error": f"Failed to get teams: {e!s}"}
