"""
Data models for the unified agent application.
This module defines the data models used by the application, including settings, workflows, PR reviews, and requirements.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

# Base models
class BaseItem(BaseModel):
    """Base model for all items in the database."""
    id: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Settings models
class Settings(BaseModel):
    """Settings for the application."""
    slack_bot_token: Optional[str] = None
    slack_app_token: Optional[str] = None
    slack_channel_id: Optional[str] = None
    codegen_user_id: Optional[str] = None
    github_token: Optional[str] = None
    github_repo: Optional[str] = None
    webhook_secret: Optional[str] = None
    ngrok_auth_token: Optional[str] = None
    ngrok_domain: Optional[str] = None
    ai_provider: str = "anthropic"
    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    data_dir: str = "./data"
    docs_path: str = "./docs"
    output_dir: str = "./output"
    port: int = 8000
    interval: int = 3600
    auto_start_requirements: bool = False
    auto_review_prs: bool = False
    auto_merge_prs: bool = False
    auto_update_status: bool = True

# Workflow models
class WorkflowStatus(str, Enum):
    """Status of a workflow."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(str, Enum):
    """Status of a workflow step."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"

class WorkflowType(str, Enum):
    """Type of workflow."""
    PR_REVIEW = "pr_review"
    REQUIREMENTS = "requirements"
    PROJECT_PLAN = "project_plan"
    CUSTOM = "custom"

class WorkflowStep(BaseModel):
    """Step in a workflow."""
    id: str
    title: str
    description: Optional[str] = None
    status: StepStatus = StepStatus.PENDING
    order: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class Workflow(BaseItem):
    """Workflow for tracking a process."""
    title: str
    description: Optional[str] = None
    type: WorkflowType
    status: WorkflowStatus = WorkflowStatus.PENDING
    steps: List[WorkflowStep] = []
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# PR Review models
class PRReviewStatus(str, Enum):
    """Status of a PR review."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PRReviewComment(BaseModel):
    """Comment on a PR review."""
    id: str
    body: str
    file: Optional[str] = None
    line: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)

class PRReview(BaseItem):
    """PR review."""
    pr_number: int
    repo: str
    title: str
    description: Optional[str] = None
    status: PRReviewStatus = PRReviewStatus.PENDING
    comments: List[PRReviewComment] = []
    workflow_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Requirements models
class RequirementStatus(str, Enum):
    """Status of a requirement."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RequirementPriority(str, Enum):
    """Priority of a requirement."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Requirement(BaseItem):
    """Requirement for a project."""
    title: str
    description: str
    status: RequirementStatus = RequirementStatus.PENDING
    priority: RequirementPriority = RequirementPriority.MEDIUM
    workflow_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# Project Plan models
class ProjectPlanStatus(str, Enum):
    """Status of a project plan."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ProjectPlan(BaseItem):
    """Project plan."""
    title: str
    description: str
    status: ProjectPlanStatus = ProjectPlanStatus.PENDING
    requirements: List[str] = []  # List of requirement IDs
    workflow_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# API models
class WorkflowCreate(BaseModel):
    """Model for creating a workflow."""
    title: str
    description: Optional[str] = None
    type: WorkflowType
    steps: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = Field(default_factory=dict)

class WorkflowUpdate(BaseModel):
    """Model for updating a workflow."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    metadata: Optional[Dict[str, Any]] = None

class StepUpdate(BaseModel):
    """Model for updating a workflow step."""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[StepStatus] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class PRReviewCreate(BaseModel):
    """Model for creating a PR review."""
    pr_number: int
    repo: str
    title: str
    description: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class RequirementCreate(BaseModel):
    """Model for creating a requirement."""
    title: str
    description: str
    priority: RequirementPriority = RequirementPriority.MEDIUM
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ProjectPlanCreate(BaseModel):
    """Model for creating a project plan."""
    title: str
    description: str
    requirements: List[str] = []
    metadata: Dict[str, Any] = Field(default_factory=dict)