import logging
from logging import getLogger
import os
import modal
from agentgen.extensions.events.codegen_app import CodegenApp
from fastapi import Request
from agentgen.extensions.github.types.events.pull_request import PullRequestLabeledEvent, PullRequestUnlabeledEvent
from helpers import remove_bot_comments, pr_review_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

# Base image with required dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        # Core dependencies
        "langchain==0.3.22",
        "langchain-core==0.3.50",
        "langchain-anthropic==0.3.10",
        "langchain-openai==0.3.12",
        "langgraph==0.3.25",
        "langgraph-prebuilt==0.1.8",
        "langchain-xai==0.2.2",
        # Other dependencies
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_sdk",
        "pydantic>=2.0.0",
        "python-dotenv",
        "PyGithub",
    )
)

# Initialize the Codegen app with GitHub integration
app = CodegenApp(name="github-pr-review", image=base_image)

@app.github.event("pull_request:labeled")
def handle_labeled(event: PullRequestLabeledEvent):
    """Handle PR labeled events."""
    logger.info("[PULL_REQUEST:LABELED] Received pull request labeled event")
    logger.info(f"PR #{event.number} labeled with: {event.label.name}")
    logger.info(f"PR title: {event.pull_request.title}")
    
    # Trigger the PR review for any PR (not just those with "Codegen" label)
    logger.info(f"PR ID: {event.pull_request.id}")
    logger.info(f"PR title: {event.pull_request.title}")
    logger.info(f"PR number: {event.number}")
    
    # Start the review process
    result = pr_review_agent(event)
    
    # Log the review result
    if result["status"] == "success":
        logger.info(f"PR review completed successfully: {result['message']}")
    else:
        logger.error(f"PR review failed: {result['error']}")

@app.github.event("pull_request:unlabeled")
def handle_unlabeled(event: PullRequestUnlabeledEvent):
    """Handle PR unlabeled events."""
    logger.info(f"PR #{event.number} unlabeled: {event.label.name}")
    # Clean up bot comments when label is removed
    remove_bot_comments(event)

@app.function(secrets=[modal.Secret.from_dotenv()])
@modal.web_endpoint(method="POST")
def entrypoint(event: dict, request: Request):
    """Handle GitHub webhook events."""
    logger.info("[WEBHOOK] Received GitHub webhook")
    return app.github.handle(event, request)
