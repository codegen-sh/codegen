"""Development Assistant for the enhanced CI/CD flow.

This component:
1. Checks out code locally for development
2. Uses AI to generate code changes based on requirements
3. Creates PRs with detailed documentation
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

import modal
from fastapi import Request
from shared import (
    BASE_IMAGE,
    create_app,
    create_linear_client,
    create_github_client,
    create_codebase,
    create_agent,
    format_linear_message,
    has_codegen_label,
    logger,
)

# Create app
app = create_app("development-assistant")

# Define data structures
@dataclass
class CodegenTask:
    """Represents a task for the development assistant."""
    issue_id: str
    issue_title: str
    issue_description: str
    issue_url: str
    repository: str
    branch: str

# AI prompt for code generation
CODE_GENERATION_PROMPT = """
You are an expert software developer. Your task is to implement the following requirement:

{requirement}

Repository: {repository}
Branch: {branch}

Please analyze the codebase and make the necessary changes to implement this requirement.
Focus on:
1. Clean, maintainable code
2. Following the existing code style and patterns
3. Adding appropriate tests
4. Updating documentation as needed

Provide a detailed explanation of your changes and the reasoning behind them.
"""

@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class DevelopmentAssistant:
    """Handles Linear webhook events and generates code changes."""
    
    @modal.enter()
    def setup(self):
        """Set up the development assistant."""
        # Subscribe to Linear webhooks
        app.linear.subscribe_all_handlers()
        self.linear_client = create_linear_client()
        self.github_client = create_github_client()
        logger.info("Development Assistant initialized")
    
    @modal.exit()
    def cleanup(self):
        """Clean up resources."""
        app.linear.unsubscribe_all_handlers()
    
    @modal.web_endpoint(method="POST")
    @app.linear.event("Issue", should_handle=has_codegen_label)
    def handle_implementation_task(self, data: Dict[str, Any], request: Request):
        """Handle implementation tasks from Linear."""
        logger.info(f"Received Linear issue event: {data.get('action', 'unknown')}")
        
        # Extract issue details
        issue_id = data.get("data", {}).get("id")
        issue_title = data.get("data", {}).get("title", "")
        issue_description = data.get("data", {}).get("description", "")
        issue_url = data.get("url", "")
        
        if not issue_id:
            logger.error("Missing issue ID in webhook data")
            return {"status": "error", "message": "Missing issue ID"}
        
        # Check if this is an implementation task
        if not self._is_implementation_task(issue_title, issue_description):
            logger.info(f"Skipping non-implementation task: {issue_title}")
            return {"status": "skipped", "message": "Not an implementation task"}
        
        # Acknowledge receipt
        self.linear_client.comment_on_issue(
            issue_id, 
            "I'm working on implementing this task. I'll create a PR with the changes shortly. 🛠️"
        )
        
        # Extract repository and branch information
        repository, branch = self._extract_repo_info(issue_description)
        
        # Create a task object
        task = CodegenTask(
            issue_id=issue_id,
            issue_title=issue_title,
            issue_description=issue_description,
            issue_url=issue_url,
            repository=repository,
            branch=branch,
        )
        
        # Generate code changes and create PR
        pr_url = self._implement_task(task)
        
        # Update the issue with the PR link
        self.linear_client.comment_on_issue(
            issue_id,
            f"✅ Implementation complete! Please review the PR: {pr_url}"
        )
        
        return {"status": "success", "message": "Implementation complete", "pr_url": pr_url}
    
    def _is_implementation_task(self, title: str, description: str) -> bool:
        """Check if this is an implementation task."""
        # In a real implementation, this would use more sophisticated logic
        # For this example, we'll check for keywords in the title or description
        implementation_keywords = ["implement", "code", "develop", "build", "create"]
        
        title_lower = title.lower()
        description_lower = description.lower()
        
        for keyword in implementation_keywords:
            if keyword in title_lower or keyword in description_lower:
                return True
        
        return False
    
    def _extract_repo_info(self, description: str) -> tuple[str, str]:
        """Extract repository and branch information from the description."""
        # In a real implementation, this would parse the description to find repo info
        # For this example, we'll use default values
        repository = "codegen-sh/codegen"
        branch = "feature/auto-generated"
        
        # Look for repository and branch information in the description
        lines = description.split("\n")
        for line in lines:
            if line.startswith("Repository:"):
                repository = line.split(":", 1)[1].strip()
            elif line.startswith("Branch:"):
                branch = line.split(":", 1)[1].strip()
        
        return repository, branch
    
    def _implement_task(self, task: CodegenTask) -> str:
        """Implement the task and create a PR."""
        # Initialize codebase
        codebase = create_codebase(task.repository, "python")
        
        # Create a new branch
        branch_name = f"{task.branch}-{task.issue_id[:8]}"
        codebase.git.checkout("-b", branch_name)
        
        # Format the task for the agent
        query = format_linear_message(task.issue_title, task.issue_description)
        
        # Create an agent to implement the changes
        agent = create_agent(codebase)
        
        # Run the agent to implement the changes
        agent.run(query)
        
        # Create a PR with the changes
        pr_title = f"[{task.issue_id}] {task.issue_title}"
        pr_body = f"""
# {task.issue_title}

This PR implements the changes requested in Linear issue: {task.issue_url}

## Changes
- Implemented the requested functionality
- Added tests
- Updated documentation

## Related Issues
- Linear: {task.issue_url}
"""
        
        # Create the PR
        pr = codebase.github.create_pr(
            title=pr_title,
            body=pr_body,
            base="main",
            head=branch_name,
        )
        
        # Reset the codebase for the next task
        codebase.reset()
        
        return pr.html_url