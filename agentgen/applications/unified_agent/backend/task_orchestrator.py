"""
Task orchestrator module for the unified agent application.
This module provides functionality for orchestrating tasks and workflows.
"""

import logging
import threading
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union, Tuple

from .models import (
    Workflow, WorkflowStep, WorkflowStatus, StepStatus, WorkflowType,
    PRReview, PRReviewStatus, Requirement, RequirementStatus, ProjectPlan, ProjectPlanStatus
)
from .database import db
from .config import config
from .slack_integration import slack

logger = logging.getLogger(__name__)

class TaskOrchestrator:
    """Task orchestrator for the unified agent application."""
    
    def __init__(self):
        """Initialize the task orchestrator."""
        self.running = False
        self.thread = None
        self.task_handlers = {}
        self.workflow_handlers = {}
    
    def start(self) -> bool:
        """Start the task orchestrator."""
        if self.running:
            return True
        
        try:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start task orchestrator: {e}")
            self.running = False
            return False
    
    def stop(self) -> None:
        """Stop the task orchestrator."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None
    
    def _run(self) -> None:
        """Run the task orchestrator."""
        while self.running:
            try:
                # Process workflows
                self._process_workflows()
                
                # Process PR reviews
                if config.workflow.auto_review_prs:
                    self._process_pr_reviews()
                
                # Process requirements
                if config.workflow.auto_start_requirements:
                    self._process_requirements()
                
                # Sleep for a bit
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in task orchestrator: {e}")
    
    def _process_workflows(self) -> None:
        """Process workflows."""
        workflows = db.get_workflows()
        
        for workflow in workflows:
            if workflow.status == WorkflowStatus.IN_PROGRESS:
                # Check if there are any pending steps
                pending_steps = [step for step in workflow.steps if step.status == StepStatus.PENDING]
                in_progress_steps = [step for step in workflow.steps if step.status == StepStatus.IN_PROGRESS]
                
                # If there are no in-progress steps and there are pending steps, start the next step
                if not in_progress_steps and pending_steps:
                    next_step = min(pending_steps, key=lambda step: step.order)
                    self._start_workflow_step(workflow, next_step)
                
                # If there are no pending or in-progress steps, complete the workflow
                if not pending_steps and not in_progress_steps:
                    self._complete_workflow(workflow)
    
    def _process_pr_reviews(self) -> None:
        """Process PR reviews."""
        pr_reviews = db.get_pr_reviews()
        
        for pr_review in pr_reviews:
            if pr_review.status == PRReviewStatus.PENDING:
                # Create a workflow for the PR review
                workflow = self._create_pr_review_workflow(pr_review)
                
                # Update the PR review with the workflow ID
                db.update_pr_review(pr_review.id, {"status": PRReviewStatus.IN_PROGRESS, "workflow_id": workflow.id})
    
    def _process_requirements(self) -> None:
        """Process requirements."""
        requirements = db.get_requirements()
        
        for requirement in requirements:
            if requirement.status == RequirementStatus.PENDING:
                # Create a workflow for the requirement
                workflow = self._create_requirement_workflow(requirement)
                
                # Update the requirement with the workflow ID
                db.update_requirement(requirement.id, {"status": RequirementStatus.IN_PROGRESS, "workflow_id": workflow.id})
    
    def _create_pr_review_workflow(self, pr_review: PRReview) -> Workflow:
        """Create a workflow for a PR review."""
        steps = [
            WorkflowStep(
                id=str(uuid.uuid4()),
                title="Fetch PR details",
                description="Fetch the PR details from GitHub",
                status=StepStatus.PENDING,
                order=1
            ),
            WorkflowStep(
                id=str(uuid.uuid4()),
                title="Analyze PR changes",
                description="Analyze the changes in the PR",
                status=StepStatus.PENDING,
                order=2
            ),
            WorkflowStep(
                id=str(uuid.uuid4()),
                title="Generate review comments",
                description="Generate review comments for the PR",
                status=StepStatus.PENDING,
                order=3
            ),
            WorkflowStep(
                id=str(uuid.uuid4()),
                title="Submit review",
                description="Submit the review to GitHub",
                status=StepStatus.PENDING,
                order=4
            )
        ]
        
        workflow = Workflow(
            id=str(uuid.uuid4()),
            title=f"PR Review: {pr_review.title}",
            description=f"Review PR #{pr_review.pr_number} in {pr_review.repo}",
            type=WorkflowType.PR_REVIEW,
            status=WorkflowStatus.PENDING,
            steps=steps,
            metadata={"pr_review_id": pr_review.id}
        )
        
        return db.create_workflow(workflow)
    
    def _create_requirement_workflow(self, requirement: Requirement) -> Workflow:
        """Create a workflow for a requirement."""
        steps = [
            WorkflowStep(
                id=str(uuid.uuid4()),
                title="Analyze requirement",
                description="Analyze the requirement and break it down into tasks",
                status=StepStatus.PENDING,
                order=1
            ),
            WorkflowStep(
                id=str(uuid.uuid4()),
                title="Implement requirement",
                description="Implement the requirement",
                status=StepStatus.PENDING,
                order=2
            ),
            WorkflowStep(
                id=str(uuid.uuid4()),
                title="Test implementation",
                description="Test the implementation of the requirement",
                status=StepStatus.PENDING,
                order=3
            ),
            WorkflowStep(
                id=str(uuid.uuid4()),
                title="Create PR",
                description="Create a PR for the implementation",
                status=StepStatus.PENDING,
                order=4
            )
        ]
        
        workflow = Workflow(
            id=str(uuid.uuid4()),
            title=f"Requirement: {requirement.title}",
            description=requirement.description,
            type=WorkflowType.REQUIREMENTS,
            status=WorkflowStatus.PENDING,
            steps=steps,
            metadata={"requirement_id": requirement.id}
        )
        
        return db.create_workflow(workflow)
    
    def _start_workflow(self, workflow: Workflow) -> None:
        """Start a workflow."""
        if workflow.status != WorkflowStatus.PENDING:
            return
        
        # Update the workflow status
        db.update_workflow(workflow.id, {
            "status": WorkflowStatus.IN_PROGRESS,
            "started_at": datetime.now()
        })
        
        # Notify about workflow start
        if workflow.type == WorkflowType.PR_REVIEW:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if pr_review_id:
                pr_review = db.get_pr_review(pr_review_id)
                if pr_review:
                    slack.send_message(f"Starting PR review for PR #{pr_review.pr_number} in {pr_review.repo}: {pr_review.title}")
        elif workflow.type == WorkflowType.REQUIREMENTS:
            requirement_id = workflow.metadata.get("requirement_id")
            if requirement_id:
                requirement = db.get_requirement(requirement_id)
                if requirement:
                    slack.send_message(f"Starting implementation of requirement: {requirement.title}")
    
    def _start_workflow_step(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Start a workflow step."""
        # Update the step status
        db.update_workflow_step(workflow.id, step.id, {
            "status": StepStatus.IN_PROGRESS,
            "started_at": datetime.now()
        })
        
        # Notify about step start
        slack.send_message(f"Starting step: {step.title} for workflow: {workflow.title}")
        
        # Execute the step handler if registered
        step_key = f"{workflow.type.value}:{step.order}"
        if step_key in self.workflow_handlers:
            try:
                self.workflow_handlers[step_key](workflow, step)
            except Exception as e:
                logger.error(f"Error executing step handler for {step_key}: {e}")
                db.update_workflow_step(workflow.id, step.id, {
                    "status": StepStatus.FAILED,
                    "error": str(e)
                })
    
    def _complete_workflow_step(self, workflow: Workflow, step: WorkflowStep, result: Optional[Dict[str, Any]] = None) -> None:
        """Complete a workflow step."""
        # Update the step status
        db.update_workflow_step(workflow.id, step.id, {
            "status": StepStatus.COMPLETED,
            "completed_at": datetime.now(),
            "result": result
        })
        
        # Notify about step completion
        slack.send_message(f"Completed step: {step.title} for workflow: {workflow.title}")
    
    def _fail_workflow_step(self, workflow: Workflow, step: WorkflowStep, error: str) -> None:
        """Fail a workflow step."""
        # Update the step status
        db.update_workflow_step(workflow.id, step.id, {
            "status": StepStatus.FAILED,
            "error": error
        })
        
        # Notify about step failure
        slack.send_message(f"Failed step: {step.title} for workflow: {workflow.title}\nError: {error}")
    
    def _skip_workflow_step(self, workflow: Workflow, step: WorkflowStep, reason: str) -> None:
        """Skip a workflow step."""
        # Update the step status
        db.update_workflow_step(workflow.id, step.id, {
            "status": StepStatus.SKIPPED,
            "result": {"reason": reason}
        })
        
        # Notify about step skip
        slack.send_message(f"Skipped step: {step.title} for workflow: {workflow.title}\nReason: {reason}")
    
    def _complete_workflow(self, workflow: Workflow) -> None:
        """Complete a workflow."""
        # Update the workflow status
        db.update_workflow(workflow.id, {
            "status": WorkflowStatus.COMPLETED,
            "completed_at": datetime.now()
        })
        
        # Update related entities
        if workflow.type == WorkflowType.PR_REVIEW:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if pr_review_id:
                db.update_pr_review(pr_review_id, {
                    "status": PRReviewStatus.COMPLETED,
                    "completed_at": datetime.now()
                })
                
                pr_review = db.get_pr_review(pr_review_id)
                if pr_review:
                    slack.send_message(f"Completed PR review for PR #{pr_review.pr_number} in {pr_review.repo}: {pr_review.title}")
        elif workflow.type == WorkflowType.REQUIREMENTS:
            requirement_id = workflow.metadata.get("requirement_id")
            if requirement_id:
                db.update_requirement(requirement_id, {
                    "status": RequirementStatus.COMPLETED,
                    "completed_at": datetime.now()
                })
                
                requirement = db.get_requirement(requirement_id)
                if requirement:
                    slack.send_message(f"Completed implementation of requirement: {requirement.title}")
    
    def _fail_workflow(self, workflow: Workflow, error: str) -> None:
        """Fail a workflow."""
        # Update the workflow status
        db.update_workflow(workflow.id, {
            "status": WorkflowStatus.FAILED,
            "metadata": {**workflow.metadata, "error": error}
        })
        
        # Update related entities
        if workflow.type == WorkflowType.PR_REVIEW:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if pr_review_id:
                db.update_pr_review(pr_review_id, {
                    "status": PRReviewStatus.FAILED,
                    "metadata": {"error": error}
                })
                
                pr_review = db.get_pr_review(pr_review_id)
                if pr_review:
                    slack.send_message(f"Failed PR review for PR #{pr_review.pr_number} in {pr_review.repo}: {pr_review.title}\nError: {error}")
        elif workflow.type == WorkflowType.REQUIREMENTS:
            requirement_id = workflow.metadata.get("requirement_id")
            if requirement_id:
                db.update_requirement(requirement_id, {
                    "status": RequirementStatus.FAILED,
                    "metadata": {"error": error}
                })
                
                requirement = db.get_requirement(requirement_id)
                if requirement:
                    slack.send_message(f"Failed implementation of requirement: {requirement.title}\nError: {error}")
    
    def _cancel_workflow(self, workflow: Workflow, reason: str) -> None:
        """Cancel a workflow."""
        # Update the workflow status
        db.update_workflow(workflow.id, {
            "status": WorkflowStatus.CANCELLED,
            "metadata": {**workflow.metadata, "cancel_reason": reason}
        })
        
        # Notify about workflow cancellation
        slack.send_message(f"Cancelled workflow: {workflow.title}\nReason: {reason}")
    
    def register_workflow_handler(self, workflow_type: WorkflowType, step_order: int, handler: Callable[[Workflow, WorkflowStep], None]) -> None:
        """Register a workflow step handler."""
        step_key = f"{workflow_type.value}:{step_order}"
        self.workflow_handlers[step_key] = handler
    
    def create_workflow(self, title: str, description: str, workflow_type: WorkflowType, steps: List[Dict[str, Any]], metadata: Dict[str, Any] = None) -> Workflow:
        """Create a new workflow."""
        workflow_steps = []
        for i, step_data in enumerate(steps):
            step = WorkflowStep(
                id=str(uuid.uuid4()),
                title=step_data["title"],
                description=step_data.get("description"),
                status=StepStatus.PENDING,
                order=i + 1
            )
            workflow_steps.append(step)
        
        workflow = Workflow(
            id=str(uuid.uuid4()),
            title=title,
            description=description,
            type=workflow_type,
            status=WorkflowStatus.PENDING,
            steps=workflow_steps,
            metadata=metadata or {}
        )
        
        return db.create_workflow(workflow)
    
    def start_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Start a workflow."""
        workflow = db.get_workflow(workflow_id)
        if not workflow:
            return None
        
        self._start_workflow(workflow)
        return db.get_workflow(workflow_id)
    
    def complete_workflow_step(self, workflow_id: str, step_id: str, result: Optional[Dict[str, Any]] = None) -> Optional[Workflow]:
        """Complete a workflow step."""
        workflow = db.get_workflow(workflow_id)
        if not workflow:
            return None
        
        step = next((s for s in workflow.steps if s.id == step_id), None)
        if not step:
            return None
        
        self._complete_workflow_step(workflow, step, result)
        return db.get_workflow(workflow_id)
    
    def fail_workflow_step(self, workflow_id: str, step_id: str, error: str) -> Optional[Workflow]:
        """Fail a workflow step."""
        workflow = db.get_workflow(workflow_id)
        if not workflow:
            return None
        
        step = next((s for s in workflow.steps if s.id == step_id), None)
        if not step:
            return None
        
        self._fail_workflow_step(workflow, step, error)
        return db.get_workflow(workflow_id)
    
    def skip_workflow_step(self, workflow_id: str, step_id: str, reason: str) -> Optional[Workflow]:
        """Skip a workflow step."""
        workflow = db.get_workflow(workflow_id)
        if not workflow:
            return None
        
        step = next((s for s in workflow.steps if s.id == step_id), None)
        if not step:
            return None
        
        self._skip_workflow_step(workflow, step, reason)
        return db.get_workflow(workflow_id)
    
    def complete_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Complete a workflow."""
        workflow = db.get_workflow(workflow_id)
        if not workflow:
            return None
        
        self._complete_workflow(workflow)
        return db.get_workflow(workflow_id)
    
    def fail_workflow(self, workflow_id: str, error: str) -> Optional[Workflow]:
        """Fail a workflow."""
        workflow = db.get_workflow(workflow_id)
        if not workflow:
            return None
        
        self._fail_workflow(workflow, error)
        return db.get_workflow(workflow_id)
    
    def cancel_workflow(self, workflow_id: str, reason: str) -> Optional[Workflow]:
        """Cancel a workflow."""
        workflow = db.get_workflow(workflow_id)
        if not workflow:
            return None
        
        self._cancel_workflow(workflow, reason)
        return db.get_workflow(workflow_id)

# Global task orchestrator instance
task_orchestrator = TaskOrchestrator()