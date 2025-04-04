#!/usr/bin/env python3
"""
FastAPI application for the PR Review Bot.
"""

import os
import json
import logging
import hmac
import hashlib
from typing import Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException, Depends, Header
from pydantic import BaseModel
from github import Github

# Import local modules
from helpers import review_pr, get_github_client

# Configure logging
logger = logging.getLogger("pr_review_bot")

# Create FastAPI app
app = FastAPI(title="PR Review Bot")

# Webhook secret for GitHub
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "")

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
    Root endpoint for the PR Review Bot.
    """
    return {"message": "PR Review Bot is running"}

@app.post("/webhook")
async def webhook(request: Request, verified: bool = Depends(verify_signature)):
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
        
        # Review all PRs regardless of label or action
        if action in ["opened", "synchronize", "reopened", "labeled"]:
            pr_number = event["pull_request"]["number"]
            repo_name = event["repository"]["full_name"]
            
            # Review all PRs
            logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
            
            try:
                # Get GitHub token
                github_token = os.environ.get("GITHUB_TOKEN")
                
                # Review the PR
                github_client = get_github_client(github_token)
                
                result = review_pr(github_client, repo_name, pr_number)
                
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Error reviewing PR: {e}")
                return {"status": "error", "message": str(e)}
    
    return {"status": "ignored"}
