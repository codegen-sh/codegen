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
logger.info(f"Webhook secret configured: {'Yes' if WEBHOOK_SECRET else 'No'}")
if WEBHOOK_SECRET:
    # Don't log the actual secret, just log a masked version for debugging
    logger.info(f"Webhook secret length: {len(WEBHOOK_SECRET)} chars")
    logger.info(f"Webhook secret first 2 chars: {WEBHOOK_SECRET[:2]}...")

async def verify_signature(request: Request, x_hub_signature_256: Optional[str] = Header(None)):
    """
    Verify the GitHub webhook signature.
    """
    if not WEBHOOK_SECRET:
        logger.warning("No webhook secret configured - skipping signature verification")
        return True
    
    if not x_hub_signature_256:
        logger.warning("No X-Hub-Signature-256 header provided - skipping verification")
        return True
    
    logger.info(f"Verifying webhook signature: {x_hub_signature_256}")
    
    body = await request.body()
    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={signature}"
    
    # Log the first few characters of the expected signature for debugging
    logger.info(f"Expected signature starts with: sha256={signature[:10]}...")
    
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        logger.warning(f"Invalid webhook signature. Expected starts with: sha256={signature[:10]}..., Got: {x_hub_signature_256}")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    logger.info("Webhook signature verified successfully")
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
    
    # Log all headers for debugging
    headers = dict(request.headers)
    logger.info(f"Webhook headers: {json.dumps(headers, indent=2)}")
    
    try:
        event = json.loads(body)
        # Log the event for debugging (truncate if too large)
        event_str = json.dumps(event, indent=2)
        if len(event_str) > 1000:
            logger.info(f"Webhook event (truncated): {event_str[:1000]}...")
        else:
            logger.info(f"Webhook event: {event_str}")
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse webhook body as JSON: {e}")
        logger.error(f"Raw body: {body.decode('utf-8', errors='replace')}")
        return {"status": "error", "message": "Invalid JSON payload"}
    
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
                if not github_token:
                    logger.error("GITHUB_TOKEN environment variable not set")
                    return {"status": "error", "message": "GitHub token not configured"}
                
                # Review the PR
                github_client = get_github_client(github_token)
                
                result = review_pr(github_client, repo_name, pr_number)
                
                logger.info(f"PR review completed: {json.dumps(result, indent=2)}")
                return {"status": "success", "result": result}
            except Exception as e:
                logger.error(f"Error reviewing PR: {e}", exc_info=True)
                return {"status": "error", "message": str(e)}
        else:
            logger.info(f"Ignoring pull request event with action '{action}'")
    else:
        logger.info(f"Ignoring event of type '{event_type}'")
    
    return {"status": "ignored"}
