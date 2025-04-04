"""
API endpoints for the integrated agent application.
"""

import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Union, Any

from fastapi import APIRouter, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .database import JSONDatabase
from .models import (
    Document,
    PRReview,
    ProjectPlan,
    Repository,
    Requirement,
    RequirementStatus,
    SlackMessage,
)
from .slack_integration import SlackIntegration
from .task_orchestrator import TaskOrchestrator

# Create FastAPI app
app = FastAPI(title="Integrated Agent", description="API for the integrated agent application")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create database instance
DATA_DIR = os.environ.get("DATA_DIR", "./data")
db = JSONDatabase(DATA_DIR)

# Create Slack integration instance
slack_integration = None
try:
    slack_integration = SlackIntegration()
except ValueError as e:
    # Log the error but don't fail the application
    import logging
    logging.getLogger(__name__).error(f"Failed to initialize Slack integration: {e}")

# Create task orchestrator instance
task_orchestrator = TaskOrchestrator(db, slack_integration)

# Create API routers
documents_router = APIRouter(prefix="/documents", tags=["Documents"])
requirements_router = APIRouter(prefix="/requirements", tags=["Requirements"])
repositories_router = APIRouter(prefix="/repositories", tags=["Repositories"])
pr_reviews_router = APIRouter(prefix="/pr-reviews", tags=["PR Reviews"])
project_plans_router = APIRouter(prefix="/project-plans", tags=["Project Plans"])
slack_router = APIRouter(prefix="/slack", tags=["Slack"])
orchestrator_router = APIRouter(prefix="/orchestrator", tags=["Orchestrator"])


# Document API endpoints

@documents_router.post("/", response_model=Document)
async def create_document(document: Document):
    """Create a new document."""
    return db.create_document(document)


@documents_router.get("/", response_model=List[Document])
async def list_documents():
    """List all documents."""
    return db.list_documents()


@documents_router.get("/{document_id}", response_model=Document)
async def get_document(document_id: str):
    """Get a document by ID."""
    document = db.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@documents_router.put("/{document_id}", response_model=Document)
async def update_document(document_id: str, document: Document):
    """Update a document."""
    if document_id != document.id:
        raise HTTPException(status_code=400, detail="Document ID mismatch")
    
    try:
        return db.update_document(document)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@documents_router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document."""
    if not db.delete_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "success"}


@documents_router.post("/upload")
async def upload_document(
    name: str = Form(...),
    file: UploadFile = File(...),
):
    """Upload a document file."""
    content = await file.read()
    document = Document(
        id=str(uuid.uuid4()),
        name=name,
        content=content.decode("utf-8"),
        requirements=[],
    )
    return db.create_document(document)


# Requirement API endpoints

@requirements_router.post("/", response_model=Requirement)
async def create_requirement(requirement: Requirement):
    """Create a new requirement."""
    return db.create_requirement(requirement)


@requirements_router.get("/", response_model=List[Requirement])
async def list_requirements(
    status: Optional[RequirementStatus] = None,
    source_document: Optional[str] = None,
):
    """List all requirements, optionally filtered by status or source document."""
    requirements = db.list_requirements()
    
    if status:
        requirements = [r for r in requirements if r.status == status]
    
    if source_document:
        requirements = [r for r in requirements if r.source_document == source_document]
    
    return requirements


@requirements_router.get("/{requirement_id}", response_model=Requirement)
async def get_requirement(requirement_id: str):
    """Get a requirement by ID."""
    requirement = db.get_requirement(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement


@requirements_router.put("/{requirement_id}", response_model=Requirement)
async def update_requirement(requirement_id: str, requirement: Requirement):
    """Update a requirement."""
    if requirement_id != requirement.id:
        raise HTTPException(status_code=400, detail="Requirement ID mismatch")
    
    try:
        return db.update_requirement(requirement)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@requirements_router.delete("/{requirement_id}")
async def delete_requirement(requirement_id: str):
    """Delete a requirement."""
    if not db.delete_requirement(requirement_id):
        raise HTTPException(status_code=404, detail="Requirement not found")
    return {"status": "success"}


@requirements_router.post("/extract")
async def extract_requirements(document_id: str):
    """Extract requirements from a document."""
    document = db.get_document(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # TODO: Implement requirement extraction logic
    # This would use the RequirementsParser from the requirements_tracker
    
    return {"status": "success", "message": "Requirements extraction not implemented yet"}


# Repository API endpoints

@repositories_router.post("/", response_model=Repository)
async def create_repository(repository: Repository):
    """Create a new repository."""
    return db.create_repository(repository)


@repositories_router.get("/", response_model=List[Repository])
async def list_repositories():
    """List all repositories."""
    return db.list_repositories()


@repositories_router.get("/{repository_id}", response_model=Repository)
async def get_repository(repository_id: str):
    """Get a repository by ID."""
    repository = db.get_repository(repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repository


@repositories_router.put("/{repository_id}", response_model=Repository)
async def update_repository(repository_id: str, repository: Repository):
    """Update a repository."""
    if repository_id != repository.id:
        raise HTTPException(status_code=400, detail="Repository ID mismatch")
    
    try:
        return db.update_repository(repository)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@repositories_router.delete("/{repository_id}")
async def delete_repository(repository_id: str):
    """Delete a repository."""
    if not db.delete_repository(repository_id):
        raise HTTPException(status_code=404, detail="Repository not found")
    return {"status": "success"}


@repositories_router.post("/{repository_id}/setup-webhook")
async def setup_webhook(repository_id: str):
    """Set up a webhook for a repository."""
    repository = db.get_repository(repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # TODO: Implement webhook setup logic
    # This would use the webhook_manager from the pr_review_agent
    
    return {"status": "success", "message": "Webhook setup not implemented yet"}


# PR Review API endpoints

@pr_reviews_router.get("/", response_model=List[PRReview])
async def list_pr_reviews(repository: Optional[str] = None):
    """List all PR reviews, optionally filtered by repository."""
    pr_reviews = db.list_pr_reviews()
    
    if repository:
        pr_reviews = [pr for pr in pr_reviews if pr.repository == repository]
    
    return pr_reviews


@pr_reviews_router.get("/{repository}/{pr_number}", response_model=PRReview)
async def get_pr_review(repository: str, pr_number: int):
    """Get a PR review by repository and PR number."""
    pr_review = db.get_pr_review(repository, pr_number)
    if not pr_review:
        raise HTTPException(status_code=404, detail="PR review not found")
    return pr_review


@pr_reviews_router.post("/{repository}/{pr_number}/review")
async def review_pr(repository: str, pr_number: int):
    """Review a PR."""
    # TODO: Implement PR review logic
    # This would use the review_pr function from the pr_review_agent
    
    return {"status": "success", "message": "PR review not implemented yet"}


# Project Plan API endpoints

@project_plans_router.post("/", response_model=ProjectPlan)
async def create_project_plan(project_plan: ProjectPlan):
    """Create a new project plan."""
    return db.create_project_plan(project_plan)


@project_plans_router.get("/", response_model=List[ProjectPlan])
async def list_project_plans(repository: Optional[str] = None):
    """List all project plans, optionally filtered by repository."""
    project_plans = db.list_project_plans()
    
    if repository:
        project_plans = [p for p in project_plans if p.repository == repository]
    
    return project_plans


@project_plans_router.get("/{project_plan_id}", response_model=ProjectPlan)
async def get_project_plan(project_plan_id: str):
    """Get a project plan by ID."""
    project_plan = db.get_project_plan(project_plan_id)
    if not project_plan:
        raise HTTPException(status_code=404, detail="Project plan not found")
    return project_plan


@project_plans_router.put("/{project_plan_id}", response_model=ProjectPlan)
async def update_project_plan(project_plan_id: str, project_plan: ProjectPlan):
    """Update a project plan."""
    if project_plan_id != project_plan.id:
        raise HTTPException(status_code=400, detail="Project plan ID mismatch")
    
    try:
        return db.update_project_plan(project_plan)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@project_plans_router.delete("/{project_plan_id}")
async def delete_project_plan(project_plan_id: str):
    """Delete a project plan."""
    if not db.delete_project_plan(project_plan_id):
        raise HTTPException(status_code=404, detail="Project plan not found")
    return {"status": "success"}


@project_plans_router.post("/generate")
async def generate_project_plan(repository_id: str):
    """Generate a project plan for a repository."""
    repository = db.get_repository(repository_id)
    if not repository:
        raise HTTPException(status_code=404, detail="Repository not found")
    
    # TODO: Implement project plan generation logic
    # This would use an AI model to generate a project plan
    
    return {"status": "success", "message": "Project plan generation not implemented yet"}


# Slack API endpoints

@slack_router.post("/send-requirement")
async def send_requirement_to_slack(requirement_id: str, channel_id: Optional[str] = None):
    """Send a requirement to Slack."""
    if not slack_integration:
        raise HTTPException(status_code=503, detail="Slack integration not available")
    
    requirement = db.get_requirement(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    try:
        message = slack_integration.send_requirement(requirement, channel=channel_id)
        
        # Store the message in the database
        db.create_slack_message(message)
        
        return {"status": "success", "message_id": message.id}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@slack_router.post("/send-pr-review")
async def send_pr_review_to_slack(repository: str, pr_number: int, channel_id: Optional[str] = None):
    """Send a PR review notification to Slack."""
    if not slack_integration:
        raise HTTPException(status_code=503, detail="Slack integration not available")
    
    pr_review = db.get_pr_review(repository, pr_number)
    if not pr_review:
        raise HTTPException(status_code=404, detail="PR review not found")
    
    try:
        message = slack_integration.send_pr_review_notification(pr_review, channel=channel_id)
        
        # Store the message in the database
        db.create_slack_message(message)
        
        return {"status": "success", "message_id": message.id}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@slack_router.post("/send-message")
async def send_message_to_slack(
    text: str,
    channel_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    requirement_id: Optional[str] = None,
    pr_number: Optional[int] = None,
):
    """Send a message to Slack."""
    if not slack_integration:
        raise HTTPException(status_code=503, detail="Slack integration not available")
    
    try:
        message = slack_integration.send_message(
            text=text,
            channel=channel_id,
            thread_ts=thread_ts,
            requirement_id=requirement_id,
            pr_number=pr_number,
        )
        
        # Store the message in the database
        db.create_slack_message(message)
        
        return {"status": "success", "message_id": message.id}
    except ValueError as e:
        raise HTTPException(status_code=500, detail=str(e))


@slack_router.get("/messages", response_model=List[SlackMessage])
async def list_slack_messages(
    channel: Optional[str] = None,
    requirement_id: Optional[str] = None,
    pr_number: Optional[int] = None,
):
    """List all slack messages, optionally filtered by channel, requirement ID, or PR number."""
    messages = db.list_slack_messages()
    
    if channel:
        messages = [m for m in messages if m.channel == channel]
    
    if requirement_id:
        messages = [m for m in messages if m.requirement_id == requirement_id]
    
    if pr_number:
        messages = [m for m in messages if m.pr_number == pr_number]
    
    return messages


@slack_router.get("/messages/{message_id}", response_model=SlackMessage)
async def get_slack_message(message_id: str):
    """Get a Slack message by ID."""
    message = db.get_slack_message(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Slack message not found")
    return message


# Task Orchestrator API endpoints

@orchestrator_router.post("/start")
async def start_orchestrator():
    """Start the task orchestrator."""
    if not task_orchestrator:
        raise HTTPException(status_code=503, detail="Task orchestrator not available")
    
    task_orchestrator.start()
    return {"status": "success", "running": task_orchestrator.is_running()}


@orchestrator_router.post("/stop")
async def stop_orchestrator():
    """Stop the task orchestrator."""
    if not task_orchestrator:
        raise HTTPException(status_code=503, detail="Task orchestrator not available")
    
    task_orchestrator.stop()
    return {"status": "success", "running": task_orchestrator.is_running()}


@orchestrator_router.get("/status")
async def get_orchestrator_status():
    """Get the status of the task orchestrator."""
    if not task_orchestrator:
        raise HTTPException(status_code=503, detail="Task orchestrator not available")
    
    return {"status": "success", "running": task_orchestrator.is_running()}


@orchestrator_router.post("/send-next-requirement")
async def send_next_requirement():
    """Send the next requirement to Slack."""
    if not task_orchestrator:
        raise HTTPException(status_code=503, detail="Task orchestrator not available")
    
    if not task_orchestrator.is_running():
        raise HTTPException(status_code=400, detail="Task orchestrator is not running")
    
    requirement = task_orchestrator.send_next_requirement()
    if not requirement:
        return {"status": "success", "message": "No requirements to send"}
    
    return {"status": "success", "requirement_id": requirement.id}


@orchestrator_router.post("/process-pr-review")
async def process_pr_review(repository: str, pr_number: int):
    """Process a PR review."""
    if not task_orchestrator:
        raise HTTPException(status_code=503, detail="Task orchestrator not available")
    
    if not task_orchestrator.is_running():
        raise HTTPException(status_code=400, detail="Task orchestrator is not running")
    
    pr_review = db.get_pr_review(repository, pr_number)
    if not pr_review:
        raise HTTPException(status_code=404, detail="PR review not found")
    
    success = task_orchestrator.process_pr_review(pr_review)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to process PR review")
    
    return {"status": "success"}


# Register routers
app.include_router(documents_router)
app.include_router(requirements_router)
app.include_router(repositories_router)
app.include_router(pr_reviews_router)
app.include_router(project_plans_router)
app.include_router(slack_router)
app.include_router(orchestrator_router)


@app.get("/")
async def root():
    """Root endpoint for the integrated agent application."""
    return {
        "message": "Integrated Agent API",
        "version": "0.1.0",
        "endpoints": [
            "/documents",
            "/requirements",
            "/repositories",
            "/pr-reviews",
            "/project-plans",
            "/slack",
            "/orchestrator",
        ],
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "database": "connected",
        "slack_integration": "connected" if slack_integration else "disconnected",
        "task_orchestrator": "running" if task_orchestrator and task_orchestrator.is_running() else "stopped",
    }