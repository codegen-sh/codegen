"""
Task orchestrator for the unified agent application.
This module provides the task orchestrator for the application.
"""

import os
import time
import uuid
import logging
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

from .models import (
    Workflow, WorkflowStep, WorkflowStatus, StepStatus, WorkflowType,
    PRReview, PRReviewStatus, Requirement, RequirementStatus, ProjectPlan, ProjectPlanStatus
)
from .database import db
from .config import config
from .slack_integration import slack
from .agents import pr_review_agent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskOrchestrator:
    """Task orchestrator for the unified agent application."""
    
    def __init__(self):
        """Initialize the task orchestrator."""
        self.running = False
        self.thread = None
        self.step_handlers = {}
        
        # Register step handlers
        self._register_step_handlers()
    
    def _register_step_handlers(self):
        """Register step handlers for workflow steps."""
        # PR Review workflow step handlers
        self.step_handlers[f"{WorkflowType.PR_REVIEW.value}:1"] = self._handle_fetch_pr_details
        self.step_handlers[f"{WorkflowType.PR_REVIEW.value}:2"] = self._handle_analyze_pr_changes
        self.step_handlers[f"{WorkflowType.PR_REVIEW.value}:3"] = self._handle_generate_review_comments
        self.step_handlers[f"{WorkflowType.PR_REVIEW.value}:4"] = self._handle_post_review_to_github
        self.step_handlers[f"{WorkflowType.PR_REVIEW.value}:5"] = self._handle_auto_merge_pr
        
        # Requirements workflow step handlers
        self.step_handlers[f"{WorkflowType.REQUIREMENTS.value}:1"] = self._handle_analyze_requirement
        self.step_handlers[f"{WorkflowType.REQUIREMENTS.value}:2"] = self._handle_implement_requirement
        self.step_handlers[f"{WorkflowType.REQUIREMENTS.value}:3"] = self._handle_test_requirement
        
        # Project Plan workflow step handlers
        self.step_handlers[f"{WorkflowType.PROJECT_PLAN.value}:1"] = self._handle_analyze_project_plan
        self.step_handlers[f"{WorkflowType.PROJECT_PLAN.value}:2"] = self._handle_generate_tasks
        self.step_handlers[f"{WorkflowType.PROJECT_PLAN.value}:3"] = self._handle_assign_tasks
    
    def start(self):
        """Start the task orchestrator."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("Task orchestrator started")
    
    def stop(self):
        """Stop the task orchestrator."""
        if not self.running:
            return
        
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            self.thread = None
        
        logger.info("Task orchestrator stopped")
    
    def _run(self):
        """Run the task orchestrator."""
        while self.running:
            try:
                # Process workflows
                self._process_workflows()
                
                # Process PR reviews
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
                
                if not pending_steps and not in_progress_steps:
                    # All steps are completed, mark the workflow as completed
                    self._complete_workflow(workflow)
                elif not in_progress_steps and pending_steps:
                    # Start the next pending step
                    next_step = min(pending_steps, key=lambda s: s.order)
                    self._start_workflow_step(workflow, next_step)
            elif workflow.status == WorkflowStatus.PENDING:
                # Start the workflow
                self._start_workflow(workflow)
    
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
                title="Post review to GitHub",
                description="Post the review comments to GitHub",
                status=StepStatus.PENDING,
                order=4
            )
        ]
        
        # Add auto-merge step if enabled
        if config.workflow.auto_merge_prs:
            steps.append(
                WorkflowStep(
                    id=str(uuid.uuid4()),
                    title="Auto-merge PR",
                    description="Auto-merge the PR if it passes review",
                    status=StepStatus.PENDING,
                    order=5
                )
            )
        
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
                title="Test requirement",
                description="Test the implementation of the requirement",
                status=StepStatus.PENDING,
                order=3
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
        # Update the workflow status
        db.update_workflow(workflow.id, {
            "status": WorkflowStatus.IN_PROGRESS,
            "started_at": datetime.now()
        })
        
        # Notify about workflow start
        slack.send_message(f"Starting workflow: {workflow.title}")
        
        # Handle specific workflow types
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
        
        # Get the step handler
        step_key = f"{workflow.type.value}:{step.order}"
        step_handler = self.step_handlers.get(step_key)
        
        if step_handler:
            # Run the step handler in a separate thread
            thread = threading.Thread(target=step_handler, args=(workflow, step))
            thread.daemon = True
            thread.start()
        else:
            logger.warning(f"No handler found for step {step_key}")
            self._fail_workflow_step(workflow, step, f"No handler found for step {step_key}")
    
    def _complete_workflow_step(self, workflow: Workflow, step: WorkflowStep, result: Any = None) -> None:
        """Complete a workflow step."""
        # Update the step status
        db.update_workflow_step(workflow.id, step.id, {
            "status": StepStatus.COMPLETED,
            "completed_at": datetime.now(),
            "result": {"result": result} if result else {}
        })
        
        # Notify about step completion
        slack.send_message(f"Completed step: {step.title} for workflow: {workflow.title}")
        
        # Check if all steps are completed
        workflow = db.get_workflow(workflow.id)
        if workflow:
            pending_steps = [s for s in workflow.steps if s.status == StepStatus.PENDING]
            in_progress_steps = [s for s in workflow.steps if s.status == StepStatus.IN_PROGRESS]
            
            if not pending_steps and not in_progress_steps:
                self._complete_workflow(workflow)
    
    def _fail_workflow_step(self, workflow: Workflow, step: WorkflowStep, error: str) -> None:
        """Fail a workflow step."""
        # Update the step status
        db.update_workflow_step(workflow.id, step.id, {
            "status": StepStatus.FAILED,
            "completed_at": datetime.now(),
            "error": error
        })
        
        # Notify about step failure
        slack.send_message(f"Failed step: {step.title} for workflow: {workflow.title}\nError: {error}")
        
        # Fail the workflow
        self._fail_workflow(workflow, f"Step {step.title} failed: {error}")
    
    def _skip_workflow_step(self, workflow: Workflow, step: WorkflowStep, reason: str) -> None:
        """Skip a workflow step."""
        # Update the step status
        db.update_workflow_step(workflow.id, step.id, {
            "status": StepStatus.SKIPPED,
            "completed_at": datetime.now(),
            "result": {"reason": reason}
        })
        
        # Notify about step skipping
        slack.send_message(f"Skipped step: {step.title} for workflow: {workflow.title}\nReason: {reason}")
    
    def _complete_workflow(self, workflow: Workflow) -> None:
        """Complete a workflow."""
        # Update the workflow status
        db.update_workflow(workflow.id, {
            "status": WorkflowStatus.COMPLETED,
            "completed_at": datetime.now()
        })
        
        # Notify about workflow completion
        slack.send_message(f"Completed workflow: {workflow.title}")
        
        # Handle specific workflow types
        if workflow.type == WorkflowType.PR_REVIEW:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if pr_review_id:
                pr_review = db.get_pr_review(pr_review_id)
                if pr_review:
                    slack.send_message(f"Completed PR review for PR #{pr_review.pr_number} in {pr_review.repo}: {pr_review.title}")
        elif workflow.type == WorkflowType.REQUIREMENTS:
            requirement_id = workflow.metadata.get("requirement_id")
            if requirement_id:
                requirement = db.get_requirement(requirement_id)
                if requirement:
                    slack.send_message(f"Completed implementation of requirement: {requirement.title}")
    
    def _fail_workflow(self, workflow: Workflow, error: str) -> None:
        """Fail a workflow."""
        # Update the workflow status
        db.update_workflow(workflow.id, {
            "status": WorkflowStatus.FAILED,
            "completed_at": datetime.now(),
            "metadata": {
                **workflow.metadata,
                "error": error
            }
        })
        
        # Notify about workflow failure
        slack.send_message(f"Failed workflow: {workflow.title}\nError: {error}")
        
        # Handle specific workflow types
        if workflow.type == WorkflowType.PR_REVIEW:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if pr_review_id:
                db.update_pr_review(pr_review_id, {
                    "status": PRReviewStatus.FAILED,
                    "metadata": {
                        **db.get_pr_review(pr_review_id).metadata,
                        "error": error
                    }
                })
                
                pr_review = db.get_pr_review(pr_review_id)
                if pr_review:
                    slack.send_message(f"Failed PR review for PR #{pr_review.pr_number} in {pr_review.repo}: {pr_review.title}\nError: {error}")
        elif workflow.type == WorkflowType.REQUIREMENTS:
            requirement_id = workflow.metadata.get("requirement_id")
            if requirement_id:
                db.update_requirement(requirement_id, {
                    "status": RequirementStatus.FAILED,
                    "metadata": {
                        **db.get_requirement(requirement_id).metadata,
                        "error": error
                    }
                })
                
                requirement = db.get_requirement(requirement_id)
                if requirement:
                    slack.send_message(f"Failed implementation of requirement: {requirement.title}\nError: {error}")
    
    def _cancel_workflow(self, workflow: Workflow, reason: str) -> None:
        """Cancel a workflow."""
        # Update the workflow status
        db.update_workflow(workflow.id, {
            "status": WorkflowStatus.CANCELLED,
            "completed_at": datetime.now(),
            "metadata": {
                **workflow.metadata,
                "cancel_reason": reason
            }
        })
        
        # Notify about workflow cancellation
        slack.send_message(f"Cancelled workflow: {workflow.title}\nReason: {reason}")
        
        # Handle specific workflow types
        if workflow.type == WorkflowType.PR_REVIEW:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if pr_review_id:
                db.update_pr_review(pr_review_id, {
                    "status": PRReviewStatus.CANCELLED,
                    "metadata": {"cancel_reason": reason}
                })
                
                pr_review = db.get_pr_review(pr_review_id)
                if pr_review:
                    slack.send_message(f"Cancelled PR review for PR #{pr_review.pr_number} in {pr_review.repo}: {pr_review.title}\nReason: {reason}")
        elif workflow.type == WorkflowType.REQUIREMENTS:
            requirement_id = workflow.metadata.get("requirement_id")
            if requirement_id:
                db.update_requirement(requirement_id, {
                    "status": RequirementStatus.CANCELLED,
                    "metadata": {"cancel_reason": reason}
                })
                
                requirement = db.get_requirement(requirement_id)
                if requirement:
                    slack.send_message(f"Cancelled implementation of requirement: {requirement.title}\nReason: {reason}")
    
    # PR Review workflow step handlers
    def _handle_fetch_pr_details(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Fetch PR details' step."""
        try:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if not pr_review_id:
                raise ValueError("PR review ID not found in workflow metadata")
            
            pr_review = db.get_pr_review(pr_review_id)
            if not pr_review:
                raise ValueError(f"PR review with ID {pr_review_id} not found")
            
            # Update the step with PR details
            details = f"PR #{pr_review.pr_number} in {pr_review.repo}: {pr_review.title}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error fetching PR details: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    def _handle_analyze_pr_changes(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Analyze PR changes' step."""
        try:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if not pr_review_id:
                raise ValueError("PR review ID not found in workflow metadata")
            
            pr_review = db.get_pr_review(pr_review_id)
            if not pr_review:
                raise ValueError(f"PR review with ID {pr_review_id} not found")
            
            # Update the step with analysis details
            details = f"Analyzed PR #{pr_review.pr_number} in {pr_review.repo}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error analyzing PR changes: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    def _handle_generate_review_comments(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Generate review comments' step."""
        try:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if not pr_review_id:
                raise ValueError("PR review ID not found in workflow metadata")
            
            pr_review = db.get_pr_review(pr_review_id)
            if not pr_review:
                raise ValueError(f"PR review with ID {pr_review_id} not found")
            
            # Use the PR review agent to generate review comments
            review_result = pr_review_agent.review_pr(pr_review)
            
            # Update the step with review details
            details = f"Generated review for PR #{pr_review.pr_number} in {pr_review.repo}"
            if review_result.get("compliant", False):
                details += " - PR is compliant with requirements"
            else:
                details += " - PR has issues that need to be addressed"
            
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error generating review comments: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    def _handle_post_review_to_github(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Post review to GitHub' step."""
        try:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if not pr_review_id:
                raise ValueError("PR review ID not found in workflow metadata")
            
            pr_review = db.get_pr_review(pr_review_id)
            if not pr_review:
                raise ValueError(f"PR review with ID {pr_review_id} not found")
            
            # Post the review to GitHub
            result = pr_review_agent.post_review_to_github(pr_review)
            
            if not result.get("success", False):
                raise ValueError(f"Failed to post review to GitHub: {result.get('error', 'Unknown error')}")
            
            # Update the PR review with the GitHub review ID
            db.update_pr_review(pr_review_id, {
                "metadata": {
                    **pr_review.metadata,
                    "github_review_id": result.get("review_id"),
                    "github_review_state": result.get("review_state")
                }
            })
            
            # Update the step with review details
            details = f"Posted review to GitHub for PR #{pr_review.pr_number} in {pr_review.repo}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error posting review to GitHub: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    def _handle_auto_merge_pr(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Auto-merge PR' step."""
        try:
            pr_review_id = workflow.metadata.get("pr_review_id")
            if not pr_review_id:
                raise ValueError("PR review ID not found in workflow metadata")
            
            pr_review = db.get_pr_review(pr_review_id)
            if not pr_review:
                raise ValueError(f"PR review with ID {pr_review_id} not found")
            
            # Check if auto-merge is enabled
            if not config.workflow.auto_merge_prs:
                reason = "Auto-merge is disabled"
                self._skip_workflow_step(workflow, step, reason)
                return
            
            # Check if the PR review passed
            if pr_review.status != PRReviewStatus.COMPLETED:
                reason = f"PR review did not pass (status: {pr_review.status})"
                self._skip_workflow_step(workflow, step, reason)
                return
            
            # Auto-merge the PR
            result = pr_review_agent.auto_merge_pr(pr_review)
            
            if not result.get("success", False):
                reason = f"Failed to auto-merge PR: {result.get('reason', result.get('error', 'Unknown error'))}"
                self._skip_workflow_step(workflow, step, reason)
                return
            
            # Update the PR review with the merge result
            db.update_pr_review(pr_review_id, {
                "metadata": {
                    **pr_review.metadata,
                    "auto_merged": True,
                    "merge_message": result.get("message")
                }
            })
            
            # Update the step with merge details
            details = f"Auto-merged PR #{pr_review.pr_number} in {pr_review.repo}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error auto-merging PR: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    # Requirements workflow step handlers
    def _handle_analyze_requirement(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Analyze requirement' step."""
        try:
            requirement_id = workflow.metadata.get("requirement_id")
            if not requirement_id:
                raise ValueError("Requirement ID not found in workflow metadata")
            
            requirement = db.get_requirement(requirement_id)
            if not requirement:
                raise ValueError(f"Requirement with ID {requirement_id} not found")
            
            # Update the step with analysis details
            details = f"Analyzed requirement: {requirement.title}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error analyzing requirement: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    def _handle_implement_requirement(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Implement requirement' step."""
        try:
            requirement_id = workflow.metadata.get("requirement_id")
            if not requirement_id:
                raise ValueError("Requirement ID not found in workflow metadata")
            
            requirement = db.get_requirement(requirement_id)
            if not requirement:
                raise ValueError(f"Requirement with ID {requirement_id} not found")
            
            # Update the step with implementation details
            details = f"Implemented requirement: {requirement.title}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error implementing requirement: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    def _handle_test_requirement(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Test requirement' step."""
        try:
            requirement_id = workflow.metadata.get("requirement_id")
            if not requirement_id:
                raise ValueError("Requirement ID not found in workflow metadata")
            
            requirement = db.get_requirement(requirement_id)
            if not requirement:
                raise ValueError(f"Requirement with ID {requirement_id} not found")
            
            # Update the step with test details
            details = f"Tested requirement: {requirement.title}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error testing requirement: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    # Project Plan workflow step handlers
    def _handle_analyze_project_plan(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Analyze project plan' step."""
        try:
            project_plan_id = workflow.metadata.get("project_plan_id")
            if not project_plan_id:
                raise ValueError("Project plan ID not found in workflow metadata")
            
            project_plan = db.get_project_plan(project_plan_id)
            if not project_plan:
                raise ValueError(f"Project plan with ID {project_plan_id} not found")
            
            # Update the step with analysis details
            details = f"Analyzed project plan: {project_plan.title}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error analyzing project plan: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    def _handle_generate_tasks(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Generate tasks' step."""
        try:
            project_plan_id = workflow.metadata.get("project_plan_id")
            if not project_plan_id:
                raise ValueError("Project plan ID not found in workflow metadata")
            
            project_plan = db.get_project_plan(project_plan_id)
            if not project_plan:
                raise ValueError(f"Project plan with ID {project_plan_id} not found")
            
            # Update the step with task generation details
            details = f"Generated tasks for project plan: {project_plan.title}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error generating tasks: {e}")
            self._fail_workflow_step(workflow, step, str(e))
    
    def _handle_assign_tasks(self, workflow: Workflow, step: WorkflowStep) -> None:
        """Handle the 'Assign tasks' step."""
        try:
            project_plan_id = workflow.metadata.get("project_plan_id")
            if not project_plan_id:
                raise ValueError("Project plan ID not found in workflow metadata")
            
            project_plan = db.get_project_plan(project_plan_id)
            if not project_plan:
                raise ValueError(f"Project plan with ID {project_plan_id} not found")
            
            # Update the step with task assignment details
            details = f"Assigned tasks for project plan: {project_plan.title}"
            self._complete_workflow_step(workflow, step, details)
        except Exception as e:
            logger.error(f"Error assigning tasks: {e}")
            self._fail_workflow_step(workflow, step, str(e))

# Create a singleton instance
task_orchestrator = TaskOrchestrator()