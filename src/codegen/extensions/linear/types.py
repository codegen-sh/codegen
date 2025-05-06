from typing import Optional, Union

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
    user: Optional[LinearUser] = None
    # Add title field with default None to prevent AttributeError
    title: Optional[str] = None


class LinearIssue(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    priority: Optional[int] = None
    team_id: Optional[str] = None


class LinearEvent(BaseModel):
    """Represents a Linear webhook event."""

    action: str  # e.g. "create", "update", "remove"
    type: str  # e.g. "Issue", "Comment", "Project"
    data: Union[LinearIssue, LinearComment]  # The actual event data
    url: str  # URL to the resource in Linear
    created_at: Optional[str] = None  # ISO timestamp
    organization_id: Optional[str] = None
    team_id: Optional[str] = None
