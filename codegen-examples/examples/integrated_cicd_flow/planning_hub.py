"""Planning Hub component for the integrated CI/CD flow.

This component receives webhook events from Linear, analyzes tickets,
and creates development plans.
"""

import logging
import os
from typing import Dict, Any

import modal
from codegen import Codebase, CodeAgent
from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.shared.enums.programming_language import ProgrammingLanguage
from fastapi import Request

from shared.models import DevelopmentPlan, DevelopmentTask, TaskStatus
from shared.utils import (
    create_codebase,
    create_development_plan,
    format_linear_message,
    has_codegen_label,
    notify_slack,
    process_update_event,
    semantic_search,
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
app = CodegenApp(name="planning-hub")

# Default repository to analyze
DEFAULT_REPO = "codegen-sh/codegen-sdk"


@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class PlanningHub:
    """Planning Hub for analyzing Linear tickets and creating development plans."""

    codebase: Codebase

    @modal.enter()
    def initialize(self):
        """Initialize the Planning Hub."""
        # Initialize codebase
        self.codebase = create_codebase(DEFAULT_REPO, ProgrammingLanguage.PYTHON)
        
        # Subscribe to Linear webhooks
        app.linear.subscribe_all_handlers()
        
        logger.info("Planning Hub initialized")

    @modal.exit()
    def cleanup(self):
        """Clean up resources."""
        app.linear.unsubscribe_all_handlers()
        logger.info("Planning Hub cleaned up")

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
            "I'm analyzing this ticket and creating a development plan... 🧠",
        )
        
        # Create a development plan
        plan = self._create_plan(task)
        
        # Update the issue with the plan
        plan_description = self._format_plan(plan)
        linear_client.comment_on_issue(task.linear_id, plan_description)
        
        # Notify Slack
        notify_slack(
            f"New development plan created for {task.id}: {task.title}",
            "development",
        )
        
        return {"status": "success", "task_id": task.id}
    
    def _create_plan(self, task: DevelopmentTask) -> DevelopmentPlan:
        """Create a development plan for a task.
        
        Args:
            task: The development task
            
        Returns:
            A development plan
        """
        # Use CodeAgent to analyze the task
        agent = CodeAgent(self.codebase)
        query = format_linear_message(task.title, task.description)
        
        # Find relevant files
        relevant_files = semantic_search(self.codebase, query)
        logger.info(f"Found {len(relevant_files)} relevant files")
        
        # Create a development plan
        plan = create_development_plan(task, self.codebase)
        
        return plan
    
    def _format_plan(self, plan: DevelopmentPlan) -> str:
        """Format a development plan for display in Linear.
        
        Args:
            plan: The development plan
            
        Returns:
            A formatted string representation of the plan
        """
        result = "## Development Plan\n\n"
        result += f"**Task**: {plan.main_task.title}\n\n"
        result += f"**Approach**: {plan.approach}\n\n"
        result += f"**Estimated Complexity**: {plan.estimated_complexity}/10\n\n"
        
        if plan.risks:
            result += "**Potential Risks**:\n"
            for risk in plan.risks:
                result += f"- {risk}\n"
            result += "\n"
        
        if plan.dependencies:
            result += "**Dependencies**:\n"
            for dep in plan.dependencies:
                result += f"- {dep}\n"
            result += "\n"
        
        if plan.subtasks:
            result += "**Subtasks**:\n"
            for subtask in plan.subtasks:
                result += f"- {subtask.title}\n"
        
        return result


if __name__ == "__main__":
    # For local development
    modal.runner.deploy_stub("planning-hub")