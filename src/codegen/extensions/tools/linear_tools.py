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
