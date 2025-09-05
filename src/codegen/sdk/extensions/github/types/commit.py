from pydantic import BaseModel

from .author import GitHubAuthor


class GitHubCommit(BaseModel):
    id: str
    tree_id: str
    distinct: bool
    message: str
    timestamp: str
    url: str
    author: GitHubAuthor
    committer: GitHubAuthor
    added: list[str]
    removed: list[str]
    modified: list[str]
