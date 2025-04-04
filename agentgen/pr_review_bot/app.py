import logging
from logging import getLogger
import os
from fastapi import FastAPI, Request
from agentgen.extensions.github.types.events.pull_request import PullRequestLabeledEvent, PullRequestUnlabeledEvent
from helpers import remove_bot_comments, pr_review_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="GitHub PR Review Bot")

@app.post("/github/webhook")
async def github_webhook(event: dict, request: Request):
    """Handle GitHub webhook events."""
    logger.info("[WEBHOOK] Received GitHub webhook")
    
    # Extract event type and action
    event_type = request.headers.get("x-github-event")
    action = event.get("action")
    
    if event_type == "pull_request" and action == "labeled":
        logger.info("[PULL_REQUEST:LABELED] Received pull request labeled event")
        
        # Parse the event
        pr_event = PullRequestLabeledEvent.model_validate(event)
        logger.info(f"PR #{pr_event.number} labeled with: {pr_event.label.name}")
        logger.info(f"PR title: {pr_event.pull_request.title}")
        
        # Start the review process
        result = pr_review_agent(pr_event)
        
        # Log the review result
        if result["status"] == "success":
            logger.info(f"PR review completed successfully: {result['message']}")
        else:
            logger.error(f"PR review failed: {result['error']}")
            
        return {"message": "PR review initiated", "status": result["status"]}
        
    elif event_type == "pull_request" and action == "unlabeled":
        logger.info("[PULL_REQUEST:UNLABELED] Received pull request unlabeled event")
        
        # Parse the event
        pr_event = PullRequestUnlabeledEvent.model_validate(event)
        logger.info(f"PR #{pr_event.number} unlabeled: {pr_event.label.name}")
        
        # Clean up bot comments
        result = remove_bot_comments(pr_event)
        return {"message": "Bot comments removed", "status": result["status"]}
    
    return {"message": "Event not handled"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
