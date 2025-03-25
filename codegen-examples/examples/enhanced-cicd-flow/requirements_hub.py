"""Requirements & Planning Hub for the enhanced CI/CD flow.

This component:
1. Captures and analyzes requirements from Linear
2. Breaks down complex tasks into manageable subtasks
3. Creates a development plan with dependencies
"""

import os
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import modal
from fastapi import Request
from shared import (
    BASE_IMAGE, 
    create_app, 
    create_linear_client, 
    has_codegen_label, 
    logger,
)

# Create app
app = create_app("requirements-hub")

# Define data structures
@dataclass
class Task:
    """Represents a development task."""
    title: str
    description: str
    priority: str
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class DevelopmentPlan:
    """Represents a development plan with tasks."""
    title: str
    description: str
    tasks: List[Task]
    repository: str
    branch: str

# AI prompt for task breakdown
TASK_BREAKDOWN_PROMPT = """
You are an expert software architect and project planner. Your task is to analyze the following requirement and break it down into smaller, manageable tasks.

For each task:
1. Provide a clear title
2. Write a detailed description
3. Assign a priority (High, Medium, Low)
4. Identify dependencies between tasks

Requirement:
{requirement}

Please format your response as a structured plan with clear tasks and dependencies.
"""

@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class RequirementsHub:
    """Handles Linear webhook events and processes requirements."""
    
    @modal.enter()
    def setup(self):
        """Set up the requirements hub."""
        # Subscribe to Linear webhooks
        app.linear.subscribe_all_handlers()
        self.linear_client = create_linear_client()
        logger.info("Requirements Hub initialized")
    
    @modal.exit()
    def cleanup(self):
        """Clean up resources."""
        app.linear.unsubscribe_all_handlers()
    
    @modal.web_endpoint(method="POST")
    @app.linear.event("Issue", should_handle=has_codegen_label)
    def handle_issue(self, data: Dict[str, Any], request: Request):
        """Handle incoming Linear issue events."""
        logger.info(f"Received Linear issue event: {data.get('action', 'unknown')}")
        
        # Extract issue details
        issue_id = data.get("data", {}).get("id")
        issue_title = data.get("data", {}).get("title", "")
        issue_description = data.get("data", {}).get("description", "")
        issue_url = data.get("url", "")
        
        if not issue_id:
            logger.error("Missing issue ID in webhook data")
            return {"status": "error", "message": "Missing issue ID"}
        
        # Acknowledge receipt
        self.linear_client.comment_on_issue(
            issue_id, 
            "I've received your request and am analyzing it to create a development plan. 🔍"
        )
        
        # Analyze the requirement and break it down into tasks
        development_plan = self._analyze_requirement(issue_title, issue_description)
        
        # Create child issues for each task
        self._create_child_issues(issue_id, development_plan)
        
        # Update the parent issue with the development plan
        self._update_parent_issue(issue_id, development_plan)
        
        return {"status": "success", "message": "Development plan created"}
    
    def _analyze_requirement(self, title: str, description: str) -> DevelopmentPlan:
        """Analyze a requirement and break it down into tasks."""
        # In a real implementation, this would use an AI model to analyze the requirement
        # For this example, we'll create a simple plan with predefined tasks
        
        # Extract repository and branch from description (if available)
        repository = "codegen-sh/codegen"  # Default repository
        branch = f"feature/{title.lower().replace(' ', '-')}"
        
        # Create a development plan with tasks
        tasks = [
            Task(
                title="Task 1: Analysis and Design",
                description="Analyze the requirements and create a detailed design document.",
                priority="High",
            ),
            Task(
                title="Task 2: Implementation",
                description="Implement the core functionality based on the design.",
                priority="High",
                dependencies=["Task 1: Analysis and Design"],
            ),
            Task(
                title="Task 3: Testing",
                description="Create and run tests to verify the implementation.",
                priority="Medium",
                dependencies=["Task 2: Implementation"],
            ),
            Task(
                title="Task 4: Documentation",
                description="Update documentation to reflect the changes.",
                priority="Low",
                dependencies=["Task 2: Implementation"],
            ),
        ]
        
        return DevelopmentPlan(
            title=title,
            description=description,
            tasks=tasks,
            repository=repository,
            branch=branch,
        )
    
    def _create_child_issues(self, parent_id: str, plan: DevelopmentPlan):
        """Create child issues for each task in the development plan."""
        for task in plan.tasks:
            # Create a child issue for the task
            child_issue = self.linear_client.create_issue(
                title=task.title,
                description=task.description,
                parent_id=parent_id,
                priority=task.priority,
            )
            
            # Add a comment with dependency information if applicable
            if task.dependencies:
                dependencies_text = "\n".join([f"- {dep}" for dep in task.dependencies])
                self.linear_client.comment_on_issue(
                    child_issue.id,
                    f"This task depends on:\n{dependencies_text}"
                )
    
    def _update_parent_issue(self, issue_id: str, plan: DevelopmentPlan):
        """Update the parent issue with the development plan."""
        # Format the development plan as markdown
        tasks_text = "\n".join([
            f"- **{task.title}** ({task.priority})\n  {task.description}"
            for task in plan.tasks
        ])
        
        plan_text = f"""
# Development Plan

## Overview
{plan.description}

## Repository
{plan.repository}

## Branch
{plan.branch}

## Tasks
{tasks_text}

## Next Steps
The tasks have been created as child issues. Please assign them to team members and track progress here.
"""
        
        # Update the parent issue with the development plan
        self.linear_client.comment_on_issue(issue_id, plan_text)
        
        # Notify that the plan is ready
        self.linear_client.comment_on_issue(
            issue_id,
            "✅ Development plan created! I've broken down the requirement into manageable tasks and created child issues for each one."
        )