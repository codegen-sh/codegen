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
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..task_orchestrator import TaskOrchestrator

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
    requirements, _, _ = orchestrator.load_state()
    return {"requirements": requirements.dict()}


@app.get("/prs")
async def get_prs():
    """
    Get all pull requests.
    """
    _, prs, _ = orchestrator.load_state()
    return {"pull_requests": prs.dict()}


@app.get("/progress")
async def get_progress():
    """
    Get the progress report.
    """
    requirements, _, _ = orchestrator.load_state()
    progress_report = orchestrator.requirements_service.generate_progress_report(requirements)
    return {"progress_report": progress_report}


@app.post("/send-requirement")
async def send_requirement(requirement_id: str):
    """
    Send a specific requirement to Codegen.
    """
    requirements, _, _ = orchestrator.load_state()
    requirement = requirements.get_requirement_by_id(requirement_id)
    
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    
    if not orchestrator.slack_service:
        raise HTTPException(status_code=400, detail="Slack service not available")
    
    orchestrator.slack_service.send_requirement_request(requirement)
    requirement.mark_in_progress()
    
    orchestrator.save_state(requirements, _, None)
    
    return {"status": "success", "message": f"Sent requirement '{requirement.description}' to Codegen"}


@app.post("/update-requirement-status")
async def update_requirement_status(requirement_id: str, status: str):
    """
    Update the status of a requirement.
    """
    requirements, prs, last_check = orchestrator.load_state()
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
    
    orchestrator.save_state(requirements, prs, last_check)
    
    return {"status": "success", "message": f"Updated requirement status to {status}"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)