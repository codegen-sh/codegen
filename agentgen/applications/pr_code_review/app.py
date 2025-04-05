#!/usr/bin/env python3
"""
PR Code Review Agent Application

A Slack-integrated PR Code Review agent that automatically reviews pull requests
against requirements and codebase patterns, and provides feedback via Slack and GitHub.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union

import uvicorn
from fastapi import FastAPI, Request, Response, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from github import Github
from github.PullRequest import PullRequest
from github.Repository import Repository

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from codegen.agents.pr_review.agent import PRReviewAgent
from codegen.agents.pr_review.single_task_request_sender import SingleTaskRequestSender
from codegen.extensions.planning.manager import PlanManager, ProjectPlan, Step, Requirement
from codegen.extensions.research.researcher import Researcher, CodeInsight, ResearchResult
from codegen.shared.logging.get_logger import get_logger

# Set up logging
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PR Code Review Agent",
    description="A Slack-integrated PR Code Review agent that automatically reviews pull requests",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables
github_token = os.environ.get("GITHUB_TOKEN", "")
slack_token = os.environ.get("SLACK_BOT_TOKEN", "")
slack_channel_id = os.environ.get("SLACK_CHANNEL_ID", "")
output_dir = os.environ.get("OUTPUT_DIR", "output")
anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY", "")
openai_api_key = os.environ.get("OPENAI_API_KEY", "")

# Initialize GitHub client
github_client = Github(github_token)

# Initialize Slack client
slack_client = WebClient(token=slack_token)

# Initialize plan manager
plan_manager = PlanManager(
    output_dir=output_dir,
    anthropic_api_key=anthropic_api_key,
    openai_api_key=openai_api_key,
)

# Initialize researcher
researcher = Researcher(
    output_dir=output_dir,
    anthropic_api_key=anthropic_api_key,
    openai_api_key=openai_api_key,
)

# Initialize task request sender
task_sender = SingleTaskRequestSender(
    slack_token=slack_token,
    slack_channel_id=slack_channel_id,
    output_dir=output_dir,
    wait_for_response=True,
    response_timeout=3600,
    github_token=github_token,
)

# Initialize PR review agent
pr_review_agent = None  # Will be initialized later with codebase

# Pydantic models for API requests and responses
class CreatePlanRequest(BaseModel):
    """Request to create a project plan."""
    
    title: str = Field(..., description="Title of the project plan")
    description: str = Field(..., description="Description of the project plan")
    markdown_url: str = Field(..., description="URL to the markdown file with requirements")
    markdown_content: Optional[str] = Field(None, description="Markdown content with requirements")

class CreatePlanResponse(BaseModel):
    """Response from creating a project plan."""
    
    status: str = Field(..., description="Status of the operation")
    plan_id: Optional[str] = Field(None, description="ID of the created plan")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class ReviewPRRequest(BaseModel):
    """Request to review a pull request."""
    
    repo_name: str = Field(..., description="Name of the repository")
    pr_number: int = Field(..., description="Number of the pull request")

class ReviewPRResponse(BaseModel):
    """Response from reviewing a pull request."""
    
    status: str = Field(..., description="Status of the operation")
    compliant: Optional[bool] = Field(None, description="Whether the PR is compliant with requirements")
    issues: Optional[List[str]] = Field(None, description="Issues found in the PR")
    suggestions: Optional[List[Union[str, Dict[str, Any]]]] = Field(None, description="Suggestions for improving the PR")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class NextStepRequest(BaseModel):
    """Request to get the next step in the plan."""
    
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the task")

class NextStepResponse(BaseModel):
    """Response from getting the next step in the plan."""
    
    status: str = Field(..., description="Status of the operation")
    step_id: Optional[str] = Field(None, description="ID of the next step")
    description: Optional[str] = Field(None, description="Description of the next step")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class UpdateStepRequest(BaseModel):
    """Request to update the status of a step."""
    
    step_id: str = Field(..., description="ID of the step to update")
    status: str = Field(..., description="New status of the step")
    pr_number: Optional[int] = Field(None, description="PR number associated with the step")
    details: Optional[str] = Field(None, description="Additional details about the step")

class UpdateStepResponse(BaseModel):
    """Response from updating the status of a step."""
    
    status: str = Field(..., description="Status of the operation")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class ProgressReportResponse(BaseModel):
    """Response from generating a progress report."""
    
    status: str = Field(..., description="Status of the operation")
    report: Optional[str] = Field(None, description="Progress report")
    error: Optional[str] = Field(None, description="Error message if operation failed")

class SlackEventRequest(BaseModel):
    """Request from Slack events API."""
    
    token: Optional[str] = Field(None, description="Verification token")
    challenge: Optional[str] = Field(None, description="Challenge for URL verification")
    type: Optional[str] = Field(None, description="Type of event")
    event: Optional[Dict[str, Any]] = Field(None, description="Event data")

class GitHubWebhookRequest(BaseModel):
    """Request from GitHub webhook."""
    
    action: Optional[str] = Field(None, description="Action that triggered the webhook")
    pull_request: Optional[Dict[str, Any]] = Field(None, description="Pull request data")
    repository: Optional[Dict[str, Any]] = Field(None, description="Repository data")

# API routes
@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "PR Code Review Agent API"}

@app.post("/create-plan", response_model=CreatePlanResponse)
async def create_plan(request: CreatePlanRequest):
    """Create a project plan from markdown content."""
    try:
        # Get markdown content from URL if not provided
        markdown_content = request.markdown_content
        if not markdown_content and request.markdown_url:
            import requests
            response = requests.get(request.markdown_url)
            response.raise_for_status()
            markdown_content = response.text
        
        if not markdown_content:
            return CreatePlanResponse(
                status="error",
                error="No markdown content provided",
            )
        
        # Create the plan
        plan = plan_manager.create_plan_from_markdown(
            markdown_content=markdown_content,
            title=request.title,
            description=request.description,
        )
        
        # Send a notification to Slack
        try:
            slack_client.chat_postMessage(
                channel=slack_channel_id,
                text=f"*Project Plan Created*\n\n*Title:* {plan.title}\n*Description:* {plan.description}\n\n*Steps:* {len(plan.steps)}\n*Requirements:* {len(plan.requirements)}",
            )
        except SlackApiError as e:
            logger.error(f"Error sending Slack notification: {e}")
        
        return CreatePlanResponse(
            status="success",
            plan_id=plan.title,
        )
    
    except Exception as e:
        logger.error(f"Error creating plan: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return CreatePlanResponse(
            status="error",
            error=str(e),
        )

@app.post("/review-pr", response_model=ReviewPRResponse)
async def review_pr(request: ReviewPRRequest):
    """Review a pull request."""
    try:
        # Initialize PR review agent if not already initialized
        global pr_review_agent
        if not pr_review_agent:
            # Create a simple codebase object for the agent
            class SimpleCodebase:
                def __init__(self, github_client, repo_name):
                    self.github_client = github_client
                    self.repo_name = repo_name
                
                def search(self, query, file_patterns=None):
                    try:
                        repo = self.github_client.get_repo(self.repo_name)
                        results = []
                        
                        # Search for code in the repository
                        code_results = self.github_client.search_code(f"repo:{self.repo_name} {query}")
                        
                        for result in code_results:
                            file_path = result.path
                            
                            # Filter by file patterns if provided
                            if file_patterns and not any(file_path.endswith(pattern) for pattern in file_patterns):
                                continue
                            
                            # Get the file content
                            try:
                                file_content = result.decoded_content.decode("utf-8")
                                
                                # Find the line number
                                line_number = None
                                for i, line in enumerate(file_content.splitlines()):
                                    if query.lower() in line.lower():
                                        line_number = i + 1
                                        break
                                
                                # Get a code snippet
                                lines = file_content.splitlines()
                                start_line = max(0, line_number - 5 if line_number else 0)
                                end_line = min(len(lines), line_number + 5 if line_number else 10)
                                code_snippet = "\n".join(lines[start_line:end_line])
                                
                                results.append({
                                    "file_path": file_path,
                                    "line_number": line_number,
                                    "code_snippet": code_snippet,
                                })
                            except Exception as e:
                                logger.error(f"Error getting file content: {e}")
                        
                        return results
                    
                    except Exception as e:
                        logger.error(f"Error searching codebase: {e}")
                        return []
            
            # Create a codebase object for the repository
            codebase = SimpleCodebase(github_client, request.repo_name)
            
            # Initialize the PR review agent
            pr_review_agent = PRReviewAgent(
                codebase=codebase,
                github_token=github_token,
                slack_token=slack_token,
                slack_channel_id=slack_channel_id,
                output_dir=output_dir,
            )
        
        # Review the PR
        result = pr_review_agent.review_pr(request.repo_name, request.pr_number)
        
        return ReviewPRResponse(
            status="success",
            compliant=result.get("compliant", False),
            issues=result.get("issues", []),
            suggestions=result.get("suggestions", []),
        )
    
    except Exception as e:
        logger.error(f"Error reviewing PR: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return ReviewPRResponse(
            status="error",
            error=str(e),
        )

@app.post("/next-step", response_model=NextStepResponse)
async def next_step(request: NextStepRequest):
    """Get the next step in the plan."""
    try:
        # Send the next step request
        result = task_sender.send_next_step_request(request.context)
        
        if result.get("status") == "error":
            return NextStepResponse(
                status="error",
                error=result.get("error", "Unknown error"),
            )
        
        return NextStepResponse(
            status="success",
            step_id=result.get("step_id"),
            description=result.get("task_description"),
        )
    
    except Exception as e:
        logger.error(f"Error getting next step: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return NextStepResponse(
            status="error",
            error=str(e),
        )

@app.post("/update-step", response_model=UpdateStepResponse)
async def update_step(request: UpdateStepRequest):
    """Update the status of a step."""
    try:
        # Update the step status
        plan_manager.update_step_status(
            step_id=request.step_id,
            status=request.status,
            pr_number=request.pr_number,
            details=request.details,
        )
        
        return UpdateStepResponse(
            status="success",
        )
    
    except Exception as e:
        logger.error(f"Error updating step: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return UpdateStepResponse(
            status="error",
            error=str(e),
        )

@app.get("/progress-report", response_model=ProgressReportResponse)
async def progress_report():
    """Generate a progress report."""
    try:
        # Generate the progress report
        report = plan_manager.generate_progress_report()
        
        # Send the progress report to Slack
        result = task_sender.send_progress_report()
        
        if result.get("status") == "error":
            logger.error(f"Error sending progress report to Slack: {result.get('error')}")
        
        return ProgressReportResponse(
            status="success",
            report=report,
        )
    
    except Exception as e:
        logger.error(f"Error generating progress report: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return ProgressReportResponse(
            status="error",
            error=str(e),
        )

@app.post("/slack/events")
async def slack_events(request: Request):
    """Handle Slack events."""
    try:
        # Get the request body
        body = await request.json()
        
        # Handle URL verification
        if body.get("type") == "url_verification":
            return {"challenge": body.get("challenge")}
        
        # Handle events
        event = body.get("event", {})
        event_type = event.get("type")
        
        if event_type == "app_mention":
            # Handle app mention
            text = event.get("text", "")
            user = event.get("user", "")
            channel = event.get("channel", "")
            ts = event.get("ts", "")
            
            # Process the command
            await process_slack_command(text, user, channel, ts)
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error handling Slack event: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {"status": "error", "error": str(e)}

@app.post("/github/webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhooks."""
    try:
        # Get the request body
        body = await request.json()
        
        # Get the event type from headers
        event_type = request.headers.get("X-GitHub-Event")
        
        if event_type == "pull_request":
            # Handle pull request event
            action = body.get("action")
            pr = body.get("pull_request", {})
            repo = body.get("repository", {})
            
            if action in ["opened", "synchronize", "reopened"]:
                # Review the PR
                repo_name = repo.get("full_name")
                pr_number = pr.get("number")
                
                if repo_name and pr_number:
                    # Send a PR review request to Slack
                    task_sender.send_pr_review_request(repo_name, pr_number)
                    
                    # Review the PR
                    await review_pr(ReviewPRRequest(repo_name=repo_name, pr_number=pr_number))
        
        return {"status": "success"}
    
    except Exception as e:
        logger.error(f"Error handling GitHub webhook: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        return {"status": "error", "error": str(e)}

async def process_slack_command(text: str, user: str, channel: str, ts: str):
    """Process a Slack command."""
    try:
        # Check if the command is for reviewing a PR
        import re
        pr_review_match = re.search(r"review PR https://github\.com/([^/]+/[^/]+)/pull/(\d+)", text, re.IGNORECASE)
        if pr_review_match:
            repo_name = pr_review_match.group(1)
            pr_number = int(pr_review_match.group(2))
            
            # Send a response
            slack_client.chat_postMessage(
                channel=channel,
                text=f"I'll review PR #{pr_number} in {repo_name} right away!",
                thread_ts=ts,
            )
            
            # Review the PR
            await review_pr(ReviewPRRequest(repo_name=repo_name, pr_number=pr_number))
            return
        
        # Check if the command is for creating a plan
        plan_match = re.search(r"create plan ([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)", text, re.IGNORECASE)
        if plan_match:
            title = plan_match.group(1).strip()
            description = plan_match.group(2).strip()
            markdown_url = plan_match.group(3).strip()
            
            # Send a response
            slack_client.chat_postMessage(
                channel=channel,
                text=f"I'll create a project plan with title: {title}",
                thread_ts=ts,
            )
            
            # Create the plan
            await create_plan(CreatePlanRequest(title=title, description=description, markdown_url=markdown_url))
            return
        
        # Check if the command is for getting the next step
        if "next step" in text.lower():
            # Send a response
            slack_client.chat_postMessage(
                channel=channel,
                text="I'll get the next step for you!",
                thread_ts=ts,
            )
            
            # Get the next step
            await next_step(NextStepRequest())
            return
        
        # Check if the command is for generating a progress report
        if "progress report" in text.lower():
            # Send a response
            slack_client.chat_postMessage(
                channel=channel,
                text="I'll generate a progress report for you!",
                thread_ts=ts,
            )
            
            # Generate the progress report
            await progress_report()
            return
        
        # If no command matched, send a help message
        slack_client.chat_postMessage(
            channel=channel,
            text="I didn't understand that command. Here are the commands I support:\n"
                 "- `@pr-review-agent review PR https://github.com/owner/repo/pull/123` - Review a PR\n"
                 "- `@pr-review-agent create plan Title | Description | https://url-to-markdown-file.md` - Create a project plan\n"
                 "- `@pr-review-agent next step` - Get the next step to implement\n"
                 "- `@pr-review-agent progress report` - Get a progress report",
            thread_ts=ts,
        )
    
    except Exception as e:
        logger.error(f"Error processing Slack command: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Send an error message
        slack_client.chat_postMessage(
            channel=channel,
            text=f"Error processing command: {str(e)}",
            thread_ts=ts,
        )

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="PR Code Review Agent")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to listen on")
    parser.add_argument("--port", type=int, default=8000, help="Port to listen on")
    parser.add_argument("--output-dir", type=str, default="output", help="Directory for output files")
    args = parser.parse_args()
    
    # Set the output directory
    global output_dir
    output_dir = args.output_dir
    
    # Create the output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Start the server
    uvicorn.run(app, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
