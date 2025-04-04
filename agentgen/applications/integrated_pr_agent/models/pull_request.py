"""
Data models for pull request tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Union

from pydantic import BaseModel, Field


class PRStatus(str, Enum):
    """Status of a pull request."""
    OPEN = "open"
    CLOSED = "closed"
    MERGED = "merged"


class PRReviewStatus(str, Enum):
    """Status of a pull request review."""
    PENDING = "pending"
    APPROVED = "approved"
    CHANGES_REQUESTED = "changes_requested"
    COMMENTED = "commented"


class PRSuggestion(BaseModel):
    """A suggestion for a pull request."""
    id: str = Field(..., description="Unique identifier for the suggestion")
    description: str = Field(..., description="Description of the suggestion")
    file_path: Optional[str] = Field(default=None, description="File path for the suggestion")
    line_number: Optional[int] = Field(default=None, description="Line number for the suggestion")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    implemented: bool = Field(default=False, description="Whether the suggestion has been implemented")


class PullRequest(BaseModel):
    """A GitHub pull request."""
    number: int = Field(..., description="PR number")
    title: str = Field(..., description="PR title")
    body: Optional[str] = Field(default=None, description="PR body")
    status: PRStatus = Field(..., description="PR status")
    review_status: PRReviewStatus = Field(default=PRReviewStatus.PENDING, description="PR review status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    author: str = Field(..., description="PR author")
    repository: str = Field(..., description="Repository name")
    base_branch: str = Field(..., description="Base branch")
    head_branch: str = Field(..., description="Head branch")
    requirement_id: Optional[str] = Field(default=None, description="Associated requirement ID")
    suggestions: List[PRSuggestion] = Field(default_factory=list, description="Suggestions for the PR")
    
    def add_suggestion(self, suggestion: PRSuggestion) -> None:
        """Add a suggestion to the PR."""
        self.suggestions.append(suggestion)
        
    def mark_suggestion_implemented(self, suggestion_id: str) -> bool:
        """Mark a suggestion as implemented."""
        for suggestion in self.suggestions:
            if suggestion.id == suggestion_id:
                suggestion.implemented = True
                return True
        return False
    
    def get_unimplemented_suggestions(self) -> List[PRSuggestion]:
        """Get all unimplemented suggestions."""
        return [s for s in self.suggestions if not s.implemented]
    
    def get_implemented_suggestions(self) -> List[PRSuggestion]:
        """Get all implemented suggestions."""
        return [s for s in self.suggestions if s.implemented]
    
    def update_review_status(self, status: PRReviewStatus) -> None:
        """Update the review status."""
        self.review_status = status
        self.updated_at = datetime.now()


class PRList(BaseModel):
    """A list of pull requests."""
    pull_requests: List[PullRequest] = Field(default_factory=list, description="List of pull requests")
    
    def add_pull_request(self, pr: PullRequest) -> None:
        """Add a pull request to the list."""
        self.pull_requests.append(pr)
    
    def get_pull_request_by_number(self, pr_number: int) -> Optional[PullRequest]:
        """Get a pull request by its number."""
        for pr in self.pull_requests:
            if pr.number == pr_number:
                return pr
        return None
    
    def get_pull_requests_by_requirement(self, requirement_id: str) -> List[PullRequest]:
        """Get all pull requests for a requirement."""
        return [pr for pr in self.pull_requests if pr.requirement_id == requirement_id]
    
    def get_open_pull_requests(self) -> List[PullRequest]:
        """Get all open pull requests."""
        return [pr for pr in self.pull_requests if pr.status == PRStatus.OPEN]
    
    def get_closed_pull_requests(self) -> List[PullRequest]:
        """Get all closed pull requests."""
        return [pr for pr in self.pull_requests if pr.status == PRStatus.CLOSED]
    
    def get_merged_pull_requests(self) -> List[PullRequest]:
        """Get all merged pull requests."""
        return [pr for pr in self.pull_requests if pr.status == PRStatus.MERGED]