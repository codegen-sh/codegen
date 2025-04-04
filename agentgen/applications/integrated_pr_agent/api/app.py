"""
FastAPI application for the Integrated PR Agent.
"""

import json
import logging
import os
import hmac
import hashlib
from typing import Dict, List, Optional, Any

import dotenv
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header, BackgroundTasks, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..task_orchestrator import TaskOrchestrator
from ..models import Document

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ],
)
logger = logging.getLogger("integrated_pr_agent")

# Create FastAPI app
app = FastAPI(title="Integrated PR Agent")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Webhook secret for GitHub
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

# Create task orchestrator
orchestrator = TaskOrchestrator(
    repo_name=os.environ.get("GITHUB_REPO", ""),
    docs_path=os.environ.get("DOCS_PATH", "docs"),
    output_dir=os.environ.get("OUTPUT_DIR", "output"),
    slack_channel_id=os.environ.get("SLACK_CHANNEL_ID", ""),
    github_token=os.environ.get("GITHUB_TOKEN", ""),
    slack_token=os.environ.get("SLACK_BOT_TOKEN", ""),
    anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
)

# Create static files directory
os.makedirs(os.path.join(os.environ.get("OUTPUT_DIR", "output"), "static"), exist_ok=True)
app.mount("/static", StaticFiles(directory=os.path.join(os.environ.get("OUTPUT_DIR", "output"), "static")), name="static")


# Request models
class DocumentRequest(BaseModel):
    """Request model for document operations."""
    title: str
    content: str
    type: str
    metadata: Optional[Dict[str, Any]] = None


class ProjectPlanRequest(BaseModel):
    """Request model for project plan generation."""
    repo_url: str
    context_doc_ids: Optional[List[str]] = None


async def verify_signature(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    """
    Verify the GitHub webhook signature.
    """
    if not WEBHOOK_SECRET or not x_hub_signature_256:
        return True
    
    body = await request.body()
    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={signature}"
    
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        logger.warning("Invalid webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    return True


@app.get("/")
async def root():
    """
    Root endpoint for the Integrated PR Agent.
    """
    return {"message": "Integrated PR Agent is running"}


@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks, verified: bool = Depends(verify_signature)):
    """
    GitHub webhook endpoint.
    """
    body = await request.body()
    event = json.loads(body)
    
    # Get the event type from the headers
    event_type = request.headers.get("X-GitHub-Event", "")
    
    logger.info(f"Received {event_type} event")
    
    # Handle pull request events
    if event_type == "pull_request":
        action = event.get("action", "")
        logger.info(f"Pull request {action} event")
        
        if action in ["opened", "synchronize", "reopened", "labeled"]:
            # Process the PR in the background
            background_tasks.add_task(orchestrator.run_once)
            
            return {"status": "success", "message": "Processing PR in background"}
    
    return {"status": "ignored"}


@app.post("/run")
async def run_once(background_tasks: BackgroundTasks):
    """
    Run the task orchestrator once.
    """
    background_tasks.add_task(orchestrator.run_once)
    return {"status": "success", "message": "Running task orchestrator in background"}


@app.get("/requirements")
async def get_requirements():
    """
    Get all requirements.
    """
    requirements, _, documents, _ = orchestrator.load_state()
    return {"requirements": requirements.dict()}


@app.get("/prs")
async def get_prs():
    """
    Get all pull requests.
    """
    _, prs, _, _ = orchestrator.load_state()
    return {"pull_requests": prs.dict()}


@app.get("/documents")
async def get_documents():
    """
    Get all documents.
    """
    _, _, documents, _ = orchestrator.load_state()
    return {"documents": documents.dict()}


@app.get("/documents/{document_id}")
async def get_document(document_id: str):
    """
    Get a specific document.
    """
    _, _, documents, _ = orchestrator.load_state()
    document = documents.get_document_by_id(document_id)
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"document": document.dict()}


@app.post("/documents")
async def create_document(document: DocumentRequest):
    """
    Create a new document.
    """
    new_document = orchestrator.add_document(
        title=document.title,
        content=document.content,
        doc_type=document.type,
        metadata=document.metadata
    )
    
    return {"status": "success", "document": new_document.dict()}


@app.post("/documents/upload")
async def upload_document(
    title: str = Form(...),
    doc_type: str = Form(...),
    file: UploadFile = File(...)
):
    """
    Upload a document file.
    """
    content = await file.read()
    content_str = content.decode("utf-8")
    
    new_document = orchestrator.add_document(
        title=title,
        content=content_str,
        doc_type=doc_type,
        metadata={"filename": file.filename}
    )
    
    return {"status": "success", "document": new_document.dict()}


@app.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """
    Delete a document.
    """
    _, _, documents, _ = orchestrator.load_state()
    
    if not documents.remove_document(document_id):
        raise HTTPException(status_code=404, detail="Document not found")
    
    documents.save_to_file(str(orchestrator.documents_file))
    
    return {"status": "success", "message": "Document deleted"}


@app.get("/progress")
async def get_progress():
    """
    Get the progress report.
    """
    requirements, _, _, _ = orchestrator.load_state()
    progress_report = orchestrator.requirements_service.generate_progress_report(requirements)
    return {"progress_report": progress_report}


@app.post("/send-requirement")
async def send_requirement(requirement_id: str):
    """
    Send a specific requirement to Codegen.
    """
    requirements, prs, documents, _ = orchestrator.load_state()
    requirement = requirements.get_requirement_by_id(requirement_id)
    
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    if not orchestrator.slack_service:
        raise HTTPException(status_code=400, detail="Slack service not available")
    
    orchestrator.slack_service.send_requirement_request(requirement)
    requirement.mark_in_progress()
    
    orchestrator.save_state(requirements, prs, documents, None)
    
    return {"status": "success", "message": f"Sent requirement '{requirement.description}' to Codegen"}


@app.post("/update-requirement-status")
async def update_requirement_status(requirement_id: str, status: str):
    """
    Update the status of a requirement.
    """
    requirements, prs, documents, last_check = orchestrator.load_state()
    requirement = requirements.get_requirement_by_id(requirement_id)
    
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    if status == "pending":
        requirement.status = "pending"
    elif status == "in_progress":
        requirement.mark_in_progress()
    elif status == "completed":
        requirement.mark_completed()
    elif status == "failed":
        requirement.mark_failed()
    else:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    orchestrator.save_state(requirements, prs, documents, last_check)
    
    return {"status": "success", "message": f"Updated requirement status to {status}"}


@app.post("/generate-project-plan")
async def generate_project_plan(request: ProjectPlanRequest):
    """
    Generate a project plan based on requirements and context documents.
    """
    requirements, _, documents, _ = orchestrator.load_state()
    
    # Filter context documents if specified
    if request.context_doc_ids:
        filtered_docs = documents.__class__()
        for doc_id in request.context_doc_ids:
            doc = documents.get_document_by_id(doc_id)
            if doc:
                filtered_docs.add_document(doc)
        context_docs = filtered_docs
    else:
        context_docs = documents
    
    # Generate the plan
    plan_doc = orchestrator.generate_project_plan(requirements, context_docs)
    
    if not plan_doc:
        raise HTTPException(status_code=500, detail="Failed to generate project plan")
    
    # Add the plan to the documents
    _, _, documents, _ = orchestrator.load_state()
    documents.add_document(plan_doc)
    documents.save_to_file(str(orchestrator.documents_file))
    
    return {"status": "success", "plan": plan_doc.dict()}


@app.post("/generate-progress-document")
async def generate_progress_document():
    """
    Generate a progress tracking document.
    """
    requirements, prs, documents, _ = orchestrator.load_state()
    
    # Generate the progress document
    progress_doc = orchestrator.generate_progress_document(requirements, prs, documents)
    
    if not progress_doc:
        raise HTTPException(status_code=500, detail="Failed to generate progress document")
    
    # Add the progress document to the documents
    documents.add_document(progress_doc)
    documents.save_to_file(str(orchestrator.documents_file))
    
    return {"status": "success", "progress_document": progress_doc.dict()}


@app.get("/download/{filename}")
async def download_file(filename: str):
    """
    Download a file from the output directory.
    """
    file_path = os.path.join(orchestrator.output_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(file_path, filename=filename)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)