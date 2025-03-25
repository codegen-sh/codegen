"""Data models for the integrated CI/CD flow."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional


class TaskStatus(str, Enum):
    """Status of a development task."""

    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class DevelopmentTask:
    """A development task derived from a Linear ticket."""

    id: str
    title: str
    description: str
    status: TaskStatus
    linear_id: str
    linear_url: str
    github_pr_url: Optional[str] = None
    subtasks: List["DevelopmentTask"] = None

    def __post_init__(self):
        """Initialize subtasks if None."""
        if self.subtasks is None:
            self.subtasks = []


@dataclass
class CodeReviewFeedback:
    """Feedback from a code review."""

    pr_url: str
    overall_assessment: str
    suggestions: List[str]
    security_issues: List[str]
    performance_issues: List[str]
    style_issues: List[str]
    positive_aspects: List[str]


@dataclass
class DevelopmentPlan:
    """A plan for implementing a feature or fixing a bug."""

    main_task: DevelopmentTask
    subtasks: List[DevelopmentTask]
    dependencies: List[str]  # List of task IDs that this plan depends on
    estimated_complexity: int  # 1-10 scale
    approach: str  # Description of the implementation approach
    risks: List[str]  # Potential risks or challenges