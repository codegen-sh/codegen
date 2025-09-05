from pydantic import BaseModel


class LinearUser(BaseModel):
    id: str
    name: str


class LinearTeam(BaseModel):
    """Represents a Linear team."""

    id: str
    name: str
    key: str


class LinearComment(BaseModel):
    id: str
    body: str
    user: LinearUser | None = None


class LinearIssue(BaseModel):
    id: str
    title: str
    description: str | None = None
    priority: int | None = None
    team_id: str | None = None


class LinearEvent(BaseModel):
    """Represents a Linear webhook event."""

    action: str  # e.g. "create", "update", "remove"
    type: str  # e.g. "Issue", "Comment", "Project"
    data: LinearIssue | LinearComment  # The actual event data
    url: str  # URL to the resource in Linear
    created_at: str | None = None  # ISO timestamp
    organization_id: str | None = None
    team_id: str | None = None
