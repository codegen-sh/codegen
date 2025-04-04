"""
Data models for requirements tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field


class RequirementStatus(str, Enum):
    """Status of a requirement."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Requirement(BaseModel):
    """A requirement extracted from documentation."""
    id: str = Field(..., description="Unique identifier for the requirement")
    description: str = Field(..., description="Description of the requirement")
    section: str = Field(..., description="Section of the documentation")
    source: str = Field(..., description="Source document")
    status: RequirementStatus = Field(default=RequirementStatus.PENDING, description="Status of the requirement")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    assigned_pr: Optional[int] = Field(default=None, description="PR number assigned to this requirement")
    implementation_details: Optional[str] = Field(default=None, description="Implementation details")
    
    def mark_in_progress(self) -> None:
        """Mark the requirement as in progress."""
        self.status = RequirementStatus.IN_PROGRESS
        self.updated_at = datetime.now()
    
    def mark_completed(self) -> None:
        """Mark the requirement as completed."""
        self.status = RequirementStatus.COMPLETED
        self.updated_at = datetime.now()
    
    def mark_failed(self) -> None:
        """Mark the requirement as failed."""
        self.status = RequirementStatus.FAILED
        self.updated_at = datetime.now()
    
    def assign_pr(self, pr_number: int) -> None:
        """Assign a PR to this requirement."""
        self.assigned_pr = pr_number
        self.updated_at = datetime.now()


class RequirementList(BaseModel):
    """A list of requirements."""
    requirements: List[Requirement] = Field(default_factory=list, description="List of requirements")
    
    def add_requirement(self, requirement: Requirement) -> None:
        """Add a requirement to the list."""
        self.requirements.append(requirement)
    
    def get_requirement_by_id(self, requirement_id: str) -> Optional[Requirement]:
        """Get a requirement by its ID."""
        for requirement in self.requirements:
            if requirement.id == requirement_id:
                return requirement
        return None
    
    def get_pending_requirements(self) -> List[Requirement]:
        """Get all pending requirements."""
        return [r for r in self.requirements if r.status == RequirementStatus.PENDING]
    
    def get_in_progress_requirements(self) -> List[Requirement]:
        """Get all in-progress requirements."""
        return [r for r in self.requirements if r.status == RequirementStatus.IN_PROGRESS]
    
    def get_completed_requirements(self) -> List[Requirement]:
        """Get all completed requirements."""
        return [r for r in self.requirements if r.status == RequirementStatus.COMPLETED]
    
    def get_failed_requirements(self) -> List[Requirement]:
        """Get all failed requirements."""
        return [r for r in self.requirements if r.status == RequirementStatus.FAILED]