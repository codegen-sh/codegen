from typing import Optional

from pydantic import BaseModel, Field


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


class LinearAttachment(BaseModel):
    """Represents a file attachment in Linear."""

    id: str
    url: str
    title: str
    subtitle: Optional[str] = None
    size: Optional[int] = None
    content_type: Optional[str] = None
    source: Optional[str] = None
    issue_id: Optional[str] = None


class LinearUploadHeader(BaseModel):
    """Header for file upload."""

    key: str
    value: str


class LinearUploadFile(BaseModel):
    """Response from file upload request."""

    assetUrl: str
    uploadUrl: str
    headers: list[LinearUploadHeader]


class LinearUploadResponse(BaseModel):
    """Response from fileUpload mutation."""

    success: bool
    uploadFile: LinearUploadFile


class LinearEvent(BaseModel):
    """Represents a Linear webhook event."""

    action: str  # e.g. "create", "update", "remove"
    type: str  # e.g. "Issue", "Comment", "Project"
    data: LinearIssue | LinearComment  # The actual event data
    url: str  # URL to the resource in Linear
    created_at: str | None = None  # ISO timestamp
    organization_id: str | None = None
    team_id: str | None = None
    attachments: list[LinearAttachment] = Field(default_factory=list)  # Attachments associated with the event
