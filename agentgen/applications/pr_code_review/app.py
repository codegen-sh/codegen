#!/usr/bin/env python3
"""
Main application for the PR Code Review agent.
"""

import os
import logging
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from pydantic import BaseModel
import uvicorn

from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.events.pr_review_handler import register_pr_review_handlers
from codegen.extensions.planning.manager import PlanManager
from codegen.shared.logging.get_logger import get_logger

# Configure logging
logger = get_logger("pr_code_review")
logger.setLevel(logging.INFO)

# Create FastAPI app
app = FastAPI(title="PR Code Review Agent")

# Create Codegen app
codegen_app = CodegenApp()

# Register PR review handlers
register_pr_review_handlers(codegen_app)


class WebhookPayload(BaseModel):
    """GitHub webhook payload."""
    
    action: Optional[str] = None
    repository: Optional[Dict[str, Any]] = None
    pull_request: Optional[Dict[str, Any]] = None
    sender: Optional[Dict[str, Any]] = None


@app.get("/")
async def root():
    """Root endpoint for the PR Code Review Agent."""
    return {"message": "PR Code Review Agent is running"}


@app.post("/github/webhook")
async def github_webhook(request: Request):
    """GitHub webhook endpoint."""
    # Get the raw body
    body = await request.json()
    
    # Get the event type from the headers
    event_type = request.headers.get("X-GitHub-Event", "")
    
    logger.info(f"Received GitHub {event_type} event")
    
    # Handle the event
    result = await codegen_app.github.handle(body, request)
    
    return result


@app.post("/slack/events")
async def slack_events(request: Request):
    """Slack events endpoint."""
    # Get the raw body
    body = await request.json()
    
    logger.info(f"Received Slack event: {body.get('type', 'unknown')}")
    
    # Handle the event
    result = await codegen_app.slack.handle(body)
    
    return result


@app.post("/create-plan")
async def create_plan(request: Request):
    """Create a project plan from markdown content."""
    # Get the request body
    body = await request.json()
    
    title = body.get("title")
    description = body.get("description")
    markdown_content = body.get("markdown_content")
    
    if not title or not description or not markdown_content:
        raise HTTPException(status_code=400, detail="Missing required fields: title, description, markdown_content")
    
    # Initialize plan manager
    output_dir = os.environ.get("OUTPUT_DIR", "output")
    plan_manager = PlanManager(output_dir=output_dir)
    
    # Create the plan
    plan = plan_manager.create_plan_from_markdown(markdown_content, title, description)
    
    # Generate a progress report
    progress_report = plan_manager.generate_progress_report()
    
    return {
        "status": "success",
        "plan": plan.model_dump(),
        "progress_report": progress_report,
    }


@app.get("/next-step")
async def next_step():
    """Get the next pending step in the current plan."""
    # Initialize plan manager
    output_dir = os.environ.get("OUTPUT_DIR", "output")
    plan_manager = PlanManager(output_dir=output_dir)
    
    # Get the next step
    next_step = plan_manager.get_next_step()
    
    if not next_step:
        return {
            "status": "error",
            "message": "No pending steps found",
        }
    
    return {
        "status": "success",
        "step": next_step.model_dump(),
    }


@app.post("/update-step")
async def update_step(request: Request):
    """Update the status of a step in the current plan."""
    # Get the request body
    body = await request.json()
    
    step_id = body.get("step_id")
    status = body.get("status")
    pr_number = body.get("pr_number")
    details = body.get("details")
    
    if not step_id or not status:
        raise HTTPException(status_code=400, detail="Missing required fields: step_id, status")
    
    # Initialize plan manager
    output_dir = os.environ.get("OUTPUT_DIR", "output")
    plan_manager = PlanManager(output_dir=output_dir)
    
    # Update the step
    plan_manager.update_step_status(step_id, status, pr_number, details)
    
    return {
        "status": "success",
        "message": f"Step {step_id} updated to {status}",
    }


@app.get("/progress-report")
async def progress_report():
    """Generate a progress report for the current plan."""
    # Initialize plan manager
    output_dir = os.environ.get("OUTPUT_DIR", "output")
    plan_manager = PlanManager(output_dir=output_dir)
    
    # Generate a progress report
    progress_report = plan_manager.generate_progress_report()
    
    return {
        "status": "success",
        "progress_report": progress_report,
    }


def main():
    """Run the PR Code Review Agent."""
    parser = argparse.ArgumentParser(description="PR Code Review Agent")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--output-dir", type=str, default="output", help="Directory for output files")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Set environment variables
    os.environ["OUTPUT_DIR"] = args.output_dir
    
    # Create output directory
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    
    # Set log level
    log_level = getattr(logging, args.log_level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # Run the server
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
