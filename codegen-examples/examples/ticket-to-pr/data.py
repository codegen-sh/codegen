from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class LinearLabels(BaseModel):
    id: str
    color: str  # hex color
    name: str


class LinearIssueUpdateEvent(BaseModel):
    action: str
    issue_id: str
    actor: Dict[str, Any]
    created_at: str
    issue_url: str
    data: Dict[str, Any]
    labels: List[LinearLabels]
    updated_from: Dict[str, Any]
    title: str
    description: Optional[str] = None
    identifier: Optional[str] = None
