"""Sentry tool for viewing Sentry issues and events."""

from typing import Any

from codegen.extensions.tools.sentry.tools import (
    view_sentry_event_details,
    view_sentry_issue_details,
    view_sentry_issues,
)
from codegen.sdk.core.codebase import Codebase


async def handle_sentry_tool(codebase: Codebase, tool_call: dict[str, Any]) -> dict[str, Any]:
    """Handle a Sentry tool call.

    Args:
        codebase: The codebase to operate on
        tool_call: The tool call parameters

    Returns:
        The tool result
    """
    action = tool_call.get("action", "view_issues")
    args = tool_call.get("args", {})

    if action == "view_issues":
        organization_slug = args.get("organization_slug", "codegen-sh")
        project_slug = args.get("project_slug")
        query = args.get("query")
        status = args.get("status", "unresolved")
        limit = args.get("limit", 20)
        cursor = args.get("cursor")

        result = view_sentry_issues(
            codebase=codebase,
            organization_slug=organization_slug,
            project_slug=project_slug,
            query=query,
            status=status,
            limit=limit,
            cursor=cursor,
        )

    elif action == "view_issue":
        issue_id = args.get("issue_id")
        if not issue_id:
            return {
                "status": "error",
                "error": "Missing required parameter: issue_id",
            }

        organization_slug = args.get("organization_slug", "codegen-sh")
        limit = args.get("limit", 10)
        cursor = args.get("cursor")

        result = view_sentry_issue_details(
            codebase=codebase,
            issue_id=issue_id,
            organization_slug=organization_slug,
            limit=limit,
            cursor=cursor,
        )

    elif action == "view_event":
        event_id = args.get("event_id")
        if not event_id:
            return {
                "status": "error",
                "error": "Missing required parameter: event_id",
            }

        organization_slug = args.get("organization_slug", "codegen-sh")
        project_slug = args.get("project_slug", "codegen")

        result = view_sentry_event_details(
            codebase=codebase,
            event_id=event_id,
            organization_slug=organization_slug,
            project_slug=project_slug,
        )

    else:
        return {
            "status": "error",
            "error": f"Unknown action: {action}. Supported actions: view_issues, view_issue, view_event",
        }

    return {
        "status": result.status,
        "error": result.error if hasattr(result, "error") and result.error else None,
        "result": result.render(),
    }


# Export the tool for use in other modules
sentry_tool = {
    "name": "ViewSentryTool",
    "description": """View Sentry issues and events.

    This tool allows you to:
    1. View a list of Sentry issues for an organization or project
    2. View details of a specific Sentry issue, including its events
    3. View details of a specific Sentry event, including stack traces

    Examples:
    - To view issues: {"action": "view_issues", "args": {"organization_slug": "codegen-sh", "project_slug": "codegen", "status": "unresolved"}}
    - To view an issue: {"action": "view_issue", "args": {"issue_id": "123456", "organization_slug": "codegen-sh"}}
    - To view an event: {"action": "view_event", "args": {"event_id": "abcdef1234567890", "organization_slug": "codegen-sh", "project_slug": "codegen"}}
    """,
    "handler": handle_sentry_tool,
}
