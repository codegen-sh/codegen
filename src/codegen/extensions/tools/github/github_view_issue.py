"""Tool for viewing GitHub issues."""

from github import Github
from github.GithubException import UnknownObjectException

from codegen.sdk.core.codebase import Codebase
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


def github_view_issue(
    codebase: Codebase,
    repo_full_name: str,
    issue_number: int,
) -> dict:
    """View a GitHub issue by its number.

    Args:
        codebase: The codebase instance
        repo_full_name: The full name of the repository (e.g., "owner/repo")
        issue_number: The issue number to view

    Returns:
        Dict containing the issue details
    """
    try:
        # Get GitHub token from environment
        token = codebase._op.access_token
        if not token:
            return {"error": "GitHub token not available"}

        # Initialize GitHub client
        g = Github(token)

        try:
            # Get repository
            repo = g.get_repo(repo_full_name)

            # Get issue
            issue = repo.get_issue(issue_number)

            # Format issue data
            issue_data = {
                "number": issue.number,
                "title": issue.title,
                "state": issue.state,
                "created_at": issue.created_at.isoformat() if issue.created_at else None,
                "updated_at": issue.updated_at.isoformat() if issue.updated_at else None,
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                "user": {
                    "login": issue.user.login,
                    "id": issue.user.id,
                    "type": issue.user.type,
                }
                if issue.user
                else None,
                "body": issue.body,
                "labels": [label.name for label in issue.labels],
                "assignees": [assignee.login for assignee in issue.assignees],
                "comments_count": issue.comments,
                "html_url": issue.html_url,
            }

            # Get comments if available
            if issue.comments > 0:
                comments = []
                for comment in issue.get_comments():
                    comments.append(
                        {
                            "id": comment.id,
                            "user": comment.user.login if comment.user else None,
                            "created_at": comment.created_at.isoformat() if comment.created_at else None,
                            "updated_at": comment.updated_at.isoformat() if comment.updated_at else None,
                            "body": comment.body,
                        }
                    )
                issue_data["comments"] = comments

            return {"success": True, "issue": issue_data}

        except UnknownObjectException:
            return {"success": False, "error": f"Issue #{issue_number} not found in repository {repo_full_name}"}
        except Exception as e:
            logger.exception(f"Error fetching GitHub issue: {e!s}")
            return {"success": False, "error": f"Error fetching GitHub issue: {e!s}"}

    except Exception as e:
        logger.exception(f"Error in github_view_issue: {e!s}")
        return {"success": False, "error": f"Error in github_view_issue: {e!s}"}
