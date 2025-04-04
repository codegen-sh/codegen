import logging
from logging import getLogger
import os
import json
from fastapi import FastAPI, Request, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import traceback

# Import local modules instead of agentgen package
from .helpers import (
    review_pr,
    get_github_client,
    get_repository,
    get_pull_request,
    post_review_comment,
    submit_review
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pr_review_bot.log"),
        logging.StreamHandler()
    ]
)
logger = getLogger("pr_review_bot")

# Create FastAPI app
app = FastAPI(title="PR Review Bot", description="GitHub PR Review Bot")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define webhook payload model
class WebhookPayload(BaseModel):
    action: str
    repository: Dict[str, Any]
    pull_request: Optional[Dict[str, Any]] = None
    issue: Optional[Dict[str, Any]] = None
    label: Optional[Dict[str, Any]] = None
    sender: Dict[str, Any]

# Global variables for ngrok
ngrok_manager = None
webhook_url_override = None

# Exception handler for all unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    logger.error(traceback.format_exc())
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": f"An unexpected error occurred: {str(exc)}",
            "type": type(exc).__name__
        }
    )

# GitHub webhook handler
@app.post("/webhook")
async def webhook(request: Request):
    # Get the raw request body
    body = await request.body()
    
    # Parse the webhook payload
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        logger.error("Invalid JSON payload")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Check event type
    event_type = request.headers.get("X-GitHub-Event")
    action = payload.get("action")
    logger.info(f"Received webhook event: {event_type}:{action}")
    
    # Process the event based on type and action
    try:
        if event_type == "pull_request":
            if action == "opened" or action == "reopened":
                # Handle PR opened event
                pr_event = get_pull_request(payload)
                logger.info(f"PR #{pr_event.number} opened: {pr_event.title}")
                
                # Process the PR
                result = review_pr(pr_event)
                return {"status": "success", "result": result}
                
            elif action == "labeled":
                # Handle PR labeled event
                pr_event = get_pull_request(payload)
                logger.info(f"PR #{pr_event.number} labeled with: {pr_event.label.name}")
                
                # Check if the label is for review
                if pr_event.label.name.lower() in ["review", "codegen", "pr-review"]:
                    # Start the review process
                    result = review_pr(pr_event)
                    return {"status": "success", "result": result}
                
                return {"status": "ignored", "message": "Label not configured for review"}
                
            elif action == "unlabeled":
                # Handle PR unlabeled event
                pr_event = get_pull_request(payload)
                logger.info(f"PR #{pr_event.number} unlabeled: {pr_event.label.name}")
                
                # Check if the label is for review
                if pr_event.label.name.lower() in ["review", "codegen", "pr-review"]:
                    # Clean up bot comments
                    result = post_review_comment(pr_event)
                    return {"status": "success", "result": result}
                
                return {"status": "ignored", "message": "Label not configured for review"}
                
            elif action == "synchronize":
                # Handle PR updated event
                logger.info(f"PR #{payload['number']} updated")
                
                # Get repository information
                repo_name = payload['repository']['full_name']
                pr_number = payload['number']
                
                # Process the PR
                github_client = get_github_client(os.environ.get("GITHUB_TOKEN", ""))
                result = review_pr(github_client, repo_name, pr_number)
                return {"status": "success", "result": result}
        
        # Return a default response for unhandled events
        return {
            "status": "ignored",
            "message": f"Event {event_type}:{action} not handled"
        }
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        logger.error(traceback.format_exc())
        # Return a 200 response to GitHub to acknowledge receipt
        # This prevents GitHub from retrying the webhook
        return {
            "status": "error", 
            "message": f"Error processing webhook: {str(e)}"
        }

# Health check endpoint
@app.get("/health")
async def health():
    return {"status": "healthy"}

# Manual review endpoint
@app.post("/review/{repo_owner}/{repo_name}/{pr_number}")
async def manual_review(
    repo_owner: str, 
    repo_name: str, 
    pr_number: int, 
    config: Config = Depends(get_config)
):
    repo_full_name = f"{repo_owner}/{repo_name}"
    
    # Process the PR
    try:
        logger.info(f"Manual review requested for PR #{pr_number} in {repo_full_name}")
        github_client = get_github_client(config.github_token)
        result = review_pr(github_client, repo_full_name, pr_number)
        logger.info(f"Manual PR review completed for #{pr_number} in {repo_full_name}")
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error processing PR: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error processing PR: {str(e)}")

# Setup webhooks endpoint
@app.post("/setup-webhooks")
async def setup_webhooks(
    background_tasks: BackgroundTasks,
    config: Config = Depends(get_config)
):
    """
    Set up webhooks for all repositories accessible by the GitHub token.
    This runs in the background to avoid timeout issues with many repositories.
    """
    webhook_manager = WebhookManager(
        get_github_client(config.github_token),
        webhook_url_override or config.webhook_url or f"http://localhost:{config.port}/webhook"
    )
    
    # Run webhook setup in background
    background_tasks.add_task(webhook_manager.setup_webhooks_for_all_repos)
    
    return {
        "status": "started",
        "message": "Webhook setup started in background. Check logs for progress."
    }

# Main entry point
if __name__ == "__main__":
    config = get_config()
    
    # Check GitHub token
    if not config.github_token:
        print("\n❌ ERROR: GitHub token not provided.")
        print("Please set the GITHUB_TOKEN environment variable.")
        print("Example: export GITHUB_TOKEN=ghp_your_token_here")
        print("Make sure your token has 'admin:repo_hook' scope to create webhooks.\n")
        exit(1)
    
    print("\n🤖 Starting PR Review Bot")
    
    # Start ngrok if enabled
    if config.use_ngrok and not config.webhook_url:
        print("\n🔄 Starting ngrok tunnel...")
        ngrok_manager = NgrokManager(config.port, auth_token=config.ngrok_auth_token)
        webhook_url_override = ngrok_manager.start_tunnel()
        
        if not webhook_url_override:
            print("\n⚠️ WARNING: Failed to start ngrok tunnel.")
            print("The bot will continue to run, but webhooks may not work correctly.")
            print("Consider setting WEBHOOK_URL manually or fixing ngrok installation.\n")
    
    print(f"\n🌐 Server will run on: http://0.0.0.0:{config.port}")
    
    # Start the server
    print("\n🚀 Starting server...")
    
    # Register shutdown event to stop ngrok
    def shutdown_event():
        if ngrok_manager:
            print("\n🛑 Stopping ngrok tunnel...")
            ngrok_manager.stop_tunnel()
    
    # Start uvicorn with shutdown event
    uvicorn.run(app, host="0.0.0.0", port=config.port)
