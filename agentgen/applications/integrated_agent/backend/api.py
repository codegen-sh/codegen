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

# Create API routers
documents_router = APIRouter(prefix="/documents", tags=["Documents"])
requirements_router = APIRouter(prefix="/requirements", tags=["Requirements"])
repositories_router = APIRouter(prefix="/repositories", tags=["Repositories"])
pr_reviews_router = APIRouter(prefix="/pr-reviews", tags=["PR Reviews"])
project_plans_router = APIRouter(prefix="/project-plans", tags=["Project Plans"])
slack_router = APIRouter(prefix="/slack", tags=["Slack"])


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
async def send_requirement_to_slack(requirement_id: str, channel_id: str):
    """Send a requirement to Slack."""
    requirement = db.get_requirement(requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    # TODO: Implement Slack integration logic
    # This would use the SlackIntegration from the requirements_tracker
    
    return {"status": "success", "message": "Slack integration not implemented yet"}


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


# Register routers
app.include_router(documents_router)
app.include_router(requirements_router)
app.include_router(repositories_router)
app.include_router(pr_reviews_router)
app.include_router(project_plans_router)
app.include_router(slack_router)


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
        ],
    }