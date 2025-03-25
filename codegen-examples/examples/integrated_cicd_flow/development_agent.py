"""Development Agent component for the integrated CI/CD flow.

This component generates code changes based on Linear tickets and creates PRs.
"""

import logging
import os
from typing import Dict, Any, Optional

import modal
from codegen import Codebase, CodeAgent
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.tools.github.create_pr import create_pr
from codegen.shared.enums.programming_language import ProgrammingLanguage
from fastapi import Request

from shared.models import DevelopmentTask, TaskStatus
from shared.utils import (
    checkout_code_locally,
    create_codebase,
    format_linear_message,
    has_codegen_label,
    notify_slack,
    process_update_event,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Modal image
image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install(
    "fastapi[standard]",
    "codegen>=0.22.2",
)

# Create CodegenApp
app = CodegenApp(name="development-agent")

# Default repository to analyze
DEFAULT_REPO = "codegen-sh/codegen-sdk"


@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class DevelopmentAgent:
    """Development Agent for generating code changes and creating PRs."""

    codebase: Codebase

    @modal.enter()
    def initialize(self):
        """Initialize the Development Agent."""
        # Initialize codebase
        self.codebase = create_codebase(DEFAULT_REPO, ProgrammingLanguage.PYTHON)
        
        # Subscribe to Linear webhooks
        app.linear.subscribe_all_handlers()
        
        logger.info("Development Agent initialized")

    @modal.exit()
    def cleanup(self):
        """Clean up resources."""
        app.linear.unsubscribe_all_handlers()
        logger.info("Development Agent cleaned up")

    @modal.web_endpoint(method="POST")
    @app.linear.event("Issue", should_handle=has_codegen_label)
    def handle_issue(self, data: Dict[str, Any], request: Request):
        """Handle Linear issue events.
        
        Args:
            data: The webhook payload from Linear
            request: The FastAPI request object
            
        Returns:
            A response indicating success or failure
        """
        logger.info("Received Linear issue event")
        
        # Initialize Linear client
        linear_client = LinearClient(access_token=os.environ["LINEAR_ACCESS_TOKEN"])
        
        # Process the event
        task = process_update_event(data)
        logger.info(f"Processing task: {task.id} - {task.title}")
        
        # Comment on the issue to acknowledge receipt
        linear_client.comment_on_issue(
            task.linear_id,
            "I'm working on implementing this feature... 👨‍💻",
        )
        
        # Check out code locally (optional step for more complex scenarios)
        local_path = checkout_code_locally(DEFAULT_REPO, f"feature/{task.id}")
        logger.info(f"Checked out code to {local_path}")
        
        # Generate code changes
        pr_url = self._implement_changes(task)
        
        if pr_url:
            # Update the task with the PR URL
            task.github_pr_url = pr_url
            task.status = TaskStatus.REVIEW
            
            # Comment on the issue with the PR URL
            linear_client.comment_on_issue(
                task.linear_id,
                f"I've created a PR with the implementation: {pr_url} 🚀",
            )
            
            # Notify Slack
            notify_slack(
                f"New PR created for {task.id}: {pr_url}",
                "development",
            )
            
            return {"status": "success", "task_id": task.id, "pr_url": pr_url}
        else:
            # Update the task status
            task.status = TaskStatus.FAILED
            
            # Comment on the issue with the error
            linear_client.comment_on_issue(
                task.linear_id,
                "I encountered an error while implementing this feature. Please check the logs.",
            )
            
            return {"status": "error", "task_id": task.id, "error": "Failed to create PR"}
    
    def _implement_changes(self, task: DevelopmentTask) -> Optional[str]:
        """Implement code changes for a task.
        
        Args:
            task: The development task
            
        Returns:
            The URL of the created PR, or None if creation failed
        """
        try:
            # Use CodeAgent to implement changes
            agent = CodeAgent(self.codebase)
            query = format_linear_message(task.title, task.description)
            
            # Run the agent to make changes
            agent.run(query)
            
            # Create a PR with the changes
            pr_title = f"[{task.id}] {task.title}"
            pr_body = f"Implements {task.id}: {task.title}\n\nThis PR was automatically generated by the Development Agent.\n\nLinear Issue: {task.linear_url}"
            
            # Create the PR
            pr_result = create_pr(self.codebase, pr_title, pr_body)
            
            # Reset the codebase for the next task
            self.codebase.reset()
            
            return pr_result.url
        except Exception as e:
            logger.exception(f"Error implementing changes: {e}")
            return None


if __name__ == "__main__":
    # For local development
    modal.runner.deploy_stub("development-agent")