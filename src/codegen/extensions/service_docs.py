"""Codegen Service Documentation Tool

This module provides information about how the Codegen service works,
including how to add repositories, connect to Linear, pricing, and more.
"""

from typing import Any, Optional


def codegen_service_docs(query: Optional[str] = None) -> dict[str, Any]:
    """Returns information about how the Codegen service works.

    Args:
        query: Optional query to filter the information returned.

    Returns:
        A dictionary containing information about the Codegen service.
    """
    # This is a placeholder. The actual content will be filled in by the user.
    service_docs = {
        "description": "Codegen is an AI-powered software engineering assistant that helps developers with code analysis, refactoring, and development tasks.",
        "repositories": {
            "adding_repos": "To add an extra repository to Codegen, please contact the Codegen team with the repository details.",
            "supported_platforms": ["GitHub", "GitLab", "Bitbucket"],
        },
        "integrations": {
            "linear": {
                "setup": "To connect Codegen to Linear, you need to configure the Linear API token in your Codegen settings.",
                "capabilities": ["View issues", "Create issues", "Comment on issues", "Update issue status"],
            },
            "slack": {
                "setup": "Codegen integrates with Slack through the Slack App Directory. Install the Codegen app to your workspace.",
                "capabilities": ["Respond to messages", "Create threads", "Share code snippets"],
            },
            "github": {
                "setup": "Codegen connects to GitHub repositories through GitHub Apps. Install the Codegen GitHub App to your organization.",
                "capabilities": ["View code", "Create PRs", "Review PRs", "Comment on issues"],
            },
        },
        "pricing": {
            "plans": [
                {"name": "Free", "description": "Limited access to Codegen features"},
                {"name": "Pro", "description": "Full access to Codegen features for individual developers"},
                {"name": "Team", "description": "Codegen for teams with collaboration features"},
                {"name": "Enterprise", "description": "Custom Codegen deployment with advanced security and support"},
            ],
            "contact": "For pricing details, please contact sales@codegen.sh",
        },
        "support": {
            "documentation": "https://docs.codegen.sh",
            "contact": "support@codegen.sh",
        },
    }

    # If a query is provided, try to find the relevant information
    if query:
        query = query.lower()

        # Handle common queries
        if "repo" in query or "repository" in query or "add" in query:
            return {"repositories": service_docs["repositories"]}

        if "linear" in query or "connect" in query:
            return {"linear": service_docs["integrations"]["linear"]}

        if "cost" in query or "price" in query or "pricing" in query:
            return {"pricing": service_docs["pricing"]}

        if "slack" in query:
            return {"slack": service_docs["integrations"]["slack"]}

        if "github" in query:
            return {"github": service_docs["integrations"]["github"]}

        if "support" in query or "help" in query:
            return {"support": service_docs["support"]}

    # Return all information if no query or no match
    return service_docs
