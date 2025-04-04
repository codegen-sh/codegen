"""
Integrated PR Agent - A CI/CD application that tracks requirements, reviews PRs, and coordinates with Codegen.
"""

from .task_orchestrator import TaskOrchestrator
from .models import (
    Requirement, 
    RequirementList, 
    RequirementStatus,
    PullRequest, 
    PRList, 
    PRStatus, 
    PRReviewStatus,
    PRSuggestion
)
from .services import (
    GitHubService,
    RequirementsService,
    PRReviewService,
    SlackService
)

__version__ = "0.1.0"
__all__ = [
    "TaskOrchestrator",
    "Requirement",
    "RequirementList",
    "RequirementStatus",
    "PullRequest",
    "PRList",
    "PRStatus",
    "PRReviewStatus",
    "PRSuggestion",
    "GitHubService",
    "RequirementsService",
    "PRReviewService",
    "SlackService",
]