"""
API module for the unified agent application.
This module provides the FastAPI application and API endpoints.
"""

import os
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .models import (
    Workflow, WorkflowStep, WorkflowStatus, StepStatus, WorkflowType,
    PRReview, PRReviewStatus, Requirement, RequirementStatus, ProjectPlan, ProjectPlanStatus,
    WorkflowCreate, WorkflowUpdate, StepUpdate, PRReviewCreate, RequirementCreate, ProjectPlanCreate
)
from .database import db
from .config import config
from .slack_integration import slack
from .task_orchestrator import task_orchestrator
from .settings_api import router as settings_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the FastAPI application
app = FastAPI(title="Unified Agent API", description="API for the unified agent application")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the settings router
app.include_router(settings_router)

# Define API models
class SlackMessageRequest(BaseModel):
    """Request model for sending a Slack message."""
    text: str
    channel: Optional[str] = None
    thread_ts: Optional[str] = None

class SlackMessageResponse(BaseModel):
    """Response model for sending a Slack message."""
    success: bool
    message_ts: Optional[str] = None
    error: Optional[str] = None

class WorkflowResponse(BaseModel):
    """Response model for a workflow."""
    id: str
    title: str
    description: Optional[str] = None
    type: str
    status: str
    steps: List[Dict[str, Any]]
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class PRReviewResponse(BaseModel):
    """Response model for a PR review."""
    id: str
    pr_number: int
    repo: str
    title: str
    description: Optional[str] = None
    status: str
    comments: List[Dict[str, Any]]
    workflow_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class RequirementResponse(BaseModel):
    """Response model for a requirement."""
    id: str
    title: str
    description: str
    status: str
    priority: str
    workflow_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class ProjectPlanResponse(BaseModel):
    """Response model for a project plan."""
    id: str
    title: str
    description: str
    status: str
    requirements: List[str]
    workflow_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

# Define API endpoints
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Welcome to the Unified Agent API"}

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

# Slack endpoints
@app.post("/slack/send-message", response_model=SlackMessageResponse)
async def send_slack_message(request: SlackMessageRequest):
    """Send a message to Slack."""
    response = slack.send_message(request.text, request.channel, request.thread_ts)
    if response:
        return {"success": True, "message_ts": response.get("ts")}
    return {"success": False, "error": "Failed to send message to Slack"}

# Workflow endpoints
@app.post("/workflows", response_model=WorkflowResponse)
async def create_workflow(workflow_create: WorkflowCreate):
    """Create a new workflow."""
    workflow = task_orchestrator.create_workflow(
        workflow_create.title,
        workflow_create.description,
        workflow_create.type,
        workflow_create.steps,
        workflow_create.metadata
    )
    return workflow.dict()

@app.get("/workflows", response_model=List[WorkflowResponse])
async def get_workflows(workflow_type: Optional[str] = None):
    """Get all workflows."""
    workflows = db.get_workflows(workflow_type)
    return [workflow.dict() for workflow in workflows]

@app.get("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str):
    """Get a workflow by ID."""
    workflow = db.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.dict()

@app.put("/workflows/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: str, workflow_update: WorkflowUpdate):
    """Update a workflow."""
    workflow = db.update_workflow(workflow_id, workflow_update.dict(exclude_unset=True))
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.dict()

@app.delete("/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """Delete a workflow."""
    success = db.delete_workflow(workflow_id)
    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"success": True}

@app.post("/workflows/{workflow_id}/start", response_model=WorkflowResponse)
async def start_workflow(workflow_id: str):
    """Start a workflow."""
    workflow = task_orchestrator.start_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.dict()

@app.post("/workflows/{workflow_id}/complete", response_model=WorkflowResponse)
async def complete_workflow(workflow_id: str):
    """Complete a workflow."""
    workflow = task_orchestrator.complete_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.dict()

@app.post("/workflows/{workflow_id}/fail", response_model=WorkflowResponse)
async def fail_workflow(workflow_id: str, error: str):
    """Fail a workflow."""
    workflow = task_orchestrator.fail_workflow(workflow_id, error)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.dict()

@app.post("/workflows/{workflow_id}/cancel", response_model=WorkflowResponse)
async def cancel_workflow(workflow_id: str, reason: str):
    """Cancel a workflow."""
    workflow = task_orchestrator.cancel_workflow(workflow_id, reason)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.dict()

@app.put("/workflows/{workflow_id}/steps/{step_id}", response_model=WorkflowResponse)
async def update_workflow_step(workflow_id: str, step_id: str, step_update: StepUpdate):
    """Update a workflow step."""
    workflow = db.update_workflow_step(workflow_id, step_id, step_update.dict(exclude_unset=True))
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow or step not found")
    return workflow.dict()

@app.post("/workflows/{workflow_id}/steps/{step_id}/complete", response_model=WorkflowResponse)
async def complete_workflow_step(workflow_id: str, step_id: str, result: Optional[Dict[str, Any]] = None):
    """Complete a workflow step."""
    workflow = task_orchestrator.complete_workflow_step(workflow_id, step_id, result)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow or step not found")
    return workflow.dict()

@app.post("/workflows/{workflow_id}/steps/{step_id}/fail", response_model=WorkflowResponse)
async def fail_workflow_step(workflow_id: str, step_id: str, error: str):
    """Fail a workflow step."""
    workflow = task_orchestrator.fail_workflow_step(workflow_id, step_id, error)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow or step not found")
    return workflow.dict()

@app.post("/workflows/{workflow_id}/steps/{step_id}/skip", response_model=WorkflowResponse)
async def skip_workflow_step(workflow_id: str, step_id: str, reason: str):
    """Skip a workflow step."""
    workflow = task_orchestrator.skip_workflow_step(workflow_id, step_id, reason)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow or step not found")
    return workflow.dict()

# PR Review endpoints
@app.post("/pr-reviews", response_model=PRReviewResponse)
async def create_pr_review(pr_review_create: PRReviewCreate):
    """Create a new PR review."""
    pr_review = PRReview(
        id=str(uuid.uuid4()),
        pr_number=pr_review_create.pr_number,
        repo=pr_review_create.repo,
        title=pr_review_create.title,
        description=pr_review_create.description,
        status=PRReviewStatus.PENDING,
        comments=[],
        metadata=pr_review_create.metadata,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    pr_review = db.create_pr_review(pr_review)
    return pr_review.dict()

@app.get("/pr-reviews", response_model=List[PRReviewResponse])
async def get_pr_reviews():
    """Get all PR reviews."""
    pr_reviews = db.get_pr_reviews()
    return [pr_review.dict() for pr_review in pr_reviews]

@app.get("/pr-reviews/{pr_review_id}", response_model=PRReviewResponse)
async def get_pr_review(pr_review_id: str):
    """Get a PR review by ID."""
    pr_review = db.get_pr_review(pr_review_id)
    if not pr_review:
        raise HTTPException(status_code=404, detail="PR review not found")
    return pr_review.dict()

@app.put("/pr-reviews/{pr_review_id}", response_model=PRReviewResponse)
async def update_pr_review(pr_review_id: str, pr_review_update: Dict[str, Any]):
    """Update a PR review."""
    pr_review = db.update_pr_review(pr_review_id, pr_review_update)
    if not pr_review:
        raise HTTPException(status_code=404, detail="PR review not found")
    return pr_review.dict()

@app.delete("/pr-reviews/{pr_review_id}")
async def delete_pr_review(pr_review_id: str):
    """Delete a PR review."""
    success = db.delete_pr_review(pr_review_id)
    if not success:
        raise HTTPException(status_code=404, detail="PR review not found")
    return {"success": True}

# Requirement endpoints
@app.post("/requirements", response_model=RequirementResponse)
async def create_requirement(requirement_create: RequirementCreate):
    """Create a new requirement."""
    requirement = Requirement(
        id=str(uuid.uuid4()),
        title=requirement_create.title,
        description=requirement_create.description,
        status=RequirementStatus.PENDING,
        priority=requirement_create.priority,
        metadata=requirement_create.metadata,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    requirement = db.create_requirement(requirement)
    return requirement.dict()

@app.get("/requirements", response_model=List[RequirementResponse])
async def get_requirements():
    """Get all requirements."""
    requirements = db.get_requirements()
    return [requirement.dict() for requirement in requirements]

@app.get("/requirements/{requirement_id}", response_model=RequirementResponse)
async def get_requirement(requirement_id: str):
    """Get a requirement by ID."""
    requirement = db.get_requirement(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement.dict()

@app.put("/requirements/{requirement_id}", response_model=RequirementResponse)
async def update_requirement(requirement_id: str, requirement_update: Dict[str, Any]):
    """Update a requirement."""
    requirement = db.update_requirement(requirement_id, requirement_update)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement.dict()

@app.delete("/requirements/{requirement_id}")
async def delete_requirement(requirement_id: str):
    """Delete a requirement."""
    success = db.delete_requirement(requirement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return {"success": True}

# Project Plan endpoints
@app.post("/project-plans", response_model=ProjectPlanResponse)
async def create_project_plan(project_plan_create: ProjectPlanCreate):
    """Create a new project plan."""
    project_plan = ProjectPlan(
        id=str(uuid.uuid4()),
        title=project_plan_create.title,
        description=project_plan_create.description,
        status=ProjectPlanStatus.PENDING,
        requirements=project_plan_create.requirements,
        metadata=project_plan_create.metadata,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    project_plan = db.create_project_plan(project_plan)
    return project_plan.dict()

@app.get("/project-plans", response_model=List[ProjectPlanResponse])
async def get_project_plans():
    """Get all project plans."""
    project_plans = db.get_project_plans()
    return [project_plan.dict() for project_plan in project_plans]

@app.get("/project-plans/{project_plan_id}", response_model=ProjectPlanResponse)
async def get_project_plan(project_plan_id: str):
    """Get a project plan by ID."""
    project_plan = db.get_project_plan(project_plan_id)
    if not project_plan:
        raise HTTPException(status_code=404, detail="Project plan not found")
    return project_plan.dict()

@app.put("/project-plans/{project_plan_id}", response_model=ProjectPlanResponse)
async def update_project_plan(project_plan_id: str, project_plan_update: Dict[str, Any]):
    """Update a project plan."""
    project_plan = db.update_project_plan(project_plan_id, project_plan_update)
    if not project_plan:
        raise HTTPException(status_code=404, detail="Project plan not found")
    return project_plan.dict()

@app.delete("/project-plans/{project_plan_id}")
async def delete_project_plan(project_plan_id: str):
    """Delete a project plan."""
    success = db.delete_project_plan(project_plan_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project plan not found")
    return {"success": True}

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Startup event."""
    # Initialize the database
    os.makedirs(config.app.data_dir, exist_ok=True)
    
    # Start the task orchestrator
    task_orchestrator.start()
    
    # Start the Slack integration
    if config.slack.bot_token and config.slack.app_token:
        slack.start()
    
    logger.info("Unified Agent API started")

@app.on_event("shutdown")
async def shutdown_event():
    """Shutdown event."""
    # Stop the task orchestrator
    task_orchestrator.stop()
    
    # Stop the Slack integration
    slack.stop()
    
    logger.info("Unified Agent API stopped")