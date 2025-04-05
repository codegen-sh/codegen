#!/usr/bin/env python3
"""
FastAPI application for the PR Review Bot.
This bot reviews pull requests and automatically merges them if they are valid.
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
from helpers import review_pr, get_github_client, remove_bot_comments, pr_review_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pr_review_bot.log"),
        logging.StreamHandler()
    ]
)
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
        
        # Process the event based on action
        if action in ["opened", "synchronize", "reopened"]:
            pr_number = event["pull_request"]["number"]
            repo_name = event["repository"]["full_name"]
            
            # Review the PR
            logger.info(f"Reviewing PR #{pr_number} in {repo_name}")
            
            try:
                # Get GitHub token
                github_token = os.environ.get("GITHUB_TOKEN")
                
                # Review the PR
                github_client = get_github_client(github_token)
                
                # Use the pr_review_agent function for a more comprehensive review
                result = pr_review_agent(event)
                
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Error reviewing PR: {e}")
                return {"status": "error", "message": str(e)}
        
        # Handle labeled events
        elif action == "labeled":
            label_name = event["label"]["name"]
            pr_number = event["pull_request"]["number"]
            
            if label_name == "Codegen":
                logger.info(f"PR #{pr_number} labeled with Codegen, starting review")
                
                try:
                    # Review the PR
                    result = pr_review_agent(event)
                    return {"status": "success", "result": result}
                except Exception as e:
                    logger.error(f"Error reviewing PR: {e}")
                    return {"status": "error", "message": str(e)}
        
        # Handle unlabeled events
        elif action == "unlabeled":
            label_name = event["label"]["name"]
            pr_number = event["pull_request"]["number"]
            
            if label_name == "Codegen":
                logger.info(f"PR #{pr_number} unlabeled, removing bot comments")
                
                try:
                    # Remove bot comments
                    result = remove_bot_comments(event)
                    return {"status": "success", "result": result}
                except Exception as e:
                    logger.error(f"Error removing bot comments: {e}")
                    return {"status": "error", "message": str(e)}
    
    return {"status": "ignored"}