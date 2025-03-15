from pydantic import BaseModel

from codegen.git.models.github_named_user_context import GithubNamedUserContext
from codegen.git.models.pr_part_context import PRPartContext


class PullRequestContext(BaseModel):
    """Represents a GitHub pull request"""

    id: int
    url: str
    html_url: str
    number: int
    state: str
    title: str
    user: GithubNamedUserContext
    draft: bool
    head: PRPartContext
    base: PRPartContext
    body: str | None = None
    merged: bool | None = None
    merged_by: dict | None = None
    additions: int | None = None
    deletions: int | None = None
    changed_files: int | None = None
    webhook_data: dict | None = None

    @classmethod
    def from_payload(cls, webhook_payload: dict) -> "PullRequestContext":
        webhook_data = webhook_payload.get("pull_request", {})
        return cls(
            id=webhook_data.get("id"),
            url=webhook_data.get("url"),
            html_url=webhook_data.get("html_url"),
            number=webhook_data.get("number"),
            state=webhook_data.get("state"),
            title=webhook_data.get("title"),
            user=GithubNamedUserContext.from_payload(webhook_data.get("user", {})),
            body=webhook_data.get("body"),
            draft=webhook_data.get("draft"),
            head=PRPartContext.from_payload(webhook_data.get("head", {})),
            base=PRPartContext.from_payload(webhook_data.get("base", {})),
            merged=webhook_data.get("merged"),
            merged_by=webhook_data.get("merged_by", {}),
            additions=webhook_data.get("additions"),
            deletions=webhook_data.get("deletions"),
            changed_files=webhook_data.get("changed_files"),
            webhook_data=webhook_data,
        )
