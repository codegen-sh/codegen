from pydantic import BaseModel


class GitHubLabel(BaseModel):
    id: int
    node_id: str
    url: str
    name: str
    color: str
    default: bool
    description: str | None
