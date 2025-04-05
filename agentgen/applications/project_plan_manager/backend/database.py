"""
Database module for the unified agent application.
This module provides the database interface for the application.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Type, TypeVar, Generic

from pydantic import BaseModel, parse_obj_as

from .models import (
    Workflow, WorkflowStep, WorkflowStatus, StepStatus, WorkflowType,
    PRReview, PRReviewStatus, Requirement, RequirementStatus, ProjectPlan, ProjectPlanStatus
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Type variable for generic functions
T = TypeVar('T', bound=BaseModel)

class Database:
    """Database interface for the unified agent application."""
    
    def __init__(self, data_dir: str = "./data"):
        """Initialize the database.
        
        Args:
            data_dir: Directory to store the database files
        """
        self.data_dir = data_dir
        
        # Create the data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        
        # Create subdirectories for each data type
        os.makedirs(os.path.join(data_dir, "workflows"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "pr_reviews"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "requirements"), exist_ok=True)
        os.makedirs(os.path.join(data_dir, "project_plans"), exist_ok=True)
    
    def _save_item(self, item: BaseModel, item_type: str) -> BaseModel:
        """Save an item to the database.
        
        Args:
            item: Item to save
            item_type: Type of item (workflows, pr_reviews, requirements, project_plans)
            
        Returns:
            The saved item
        """
        # Update the updated_at field
        item.updated_at = datetime.now()
        
        # Save the item to a file
        file_path = os.path.join(self.data_dir, item_type, f"{item.id}.json")
        with open(file_path, "w") as f:
            f.write(item.json(indent=2))
        
        return item
    
    def _load_item(self, item_id: str, item_type: str, model_class: Type[T]) -> Optional[T]:
        """Load an item from the database.
        
        Args:
            item_id: ID of the item to load
            item_type: Type of item (workflows, pr_reviews, requirements, project_plans)
            model_class: Pydantic model class to parse the item as
            
        Returns:
            The loaded item, or None if not found
        """
        file_path = os.path.join(self.data_dir, item_type, f"{item_id}.json")
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            return parse_obj_as(model_class, data)
        except Exception as e:
            logger.error(f"Error loading item {item_id} of type {item_type}: {e}")
            return None
    
    def _load_items(self, item_type: str, model_class: Type[T]) -> List[T]:
        """Load all items of a specific type from the database.
        
        Args:
            item_type: Type of item (workflows, pr_reviews, requirements, project_plans)
            model_class: Pydantic model class to parse the items as
            
        Returns:
            List of loaded items
        """
        items = []
        dir_path = os.path.join(self.data_dir, item_type)
        
        if not os.path.exists(dir_path):
            return []
        
        for file_name in os.listdir(dir_path):
            if not file_name.endswith(".json"):
                continue
            
            item_id = file_name[:-5]  # Remove .json extension
            item = self._load_item(item_id, item_type, model_class)
            
            if item:
                items.append(item)
        
        return items
    
    def _delete_item(self, item_id: str, item_type: str) -> bool:
        """Delete an item from the database.
        
        Args:
            item_id: ID of the item to delete
            item_type: Type of item (workflows, pr_reviews, requirements, project_plans)
            
        Returns:
            True if the item was deleted, False otherwise
        """
        file_path = os.path.join(self.data_dir, item_type, f"{item_id}.json")
        if not os.path.exists(file_path):
            return False
        
        try:
            os.remove(file_path)
            return True
        except Exception as e:
            logger.error(f"Error deleting item {item_id} of type {item_type}: {e}")
            return False
    
    # Workflow methods
    def create_workflow(self, workflow: Workflow) -> Workflow:
        """Create a new workflow.
        
        Args:
            workflow: Workflow to create
            
        Returns:
            The created workflow
        """
        return self._save_item(workflow, "workflows")
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID.
        
        Args:
            workflow_id: ID of the workflow to get
            
        Returns:
            The workflow, or None if not found
        """
        return self._load_item(workflow_id, "workflows", Workflow)
    
    def get_workflows(self, workflow_type: Optional[str] = None) -> List[Workflow]:
        """Get all workflows.
        
        Args:
            workflow_type: Optional type of workflows to get
            
        Returns:
            List of workflows
        """
        workflows = self._load_items("workflows", Workflow)
        
        if workflow_type:
            workflows = [w for w in workflows if w.type == workflow_type]
        
        return workflows
    
    def update_workflow(self, workflow_id: str, update_data: Dict[str, Any]) -> Optional[Workflow]:
        """Update a workflow.
        
        Args:
            workflow_id: ID of the workflow to update
            update_data: Data to update
            
        Returns:
            The updated workflow, or None if not found
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        # Update the workflow
        for key, value in update_data.items():
            if hasattr(workflow, key):
                setattr(workflow, key, value)
        
        return self._save_item(workflow, "workflows")
    
    def update_workflow_step(self, workflow_id: str, step_id: str, update_data: Dict[str, Any]) -> Optional[Workflow]:
        """Update a workflow step.
        
        Args:
            workflow_id: ID of the workflow
            step_id: ID of the step to update
            update_data: Data to update
            
        Returns:
            The updated workflow, or None if not found
        """
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return None
        
        # Find the step
        step_index = None
        for i, step in enumerate(workflow.steps):
            if step.id == step_id:
                step_index = i
                break
        
        if step_index is None:
            return None
        
        # Update the step
        for key, value in update_data.items():
            if hasattr(workflow.steps[step_index], key):
                setattr(workflow.steps[step_index], key, value)
        
        return self._save_item(workflow, "workflows")
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow.
        
        Args:
            workflow_id: ID of the workflow to delete
            
        Returns:
            True if the workflow was deleted, False otherwise
        """
        return self._delete_item(workflow_id, "workflows")
    
    # PR Review methods
    def create_pr_review(self, pr_review: PRReview) -> PRReview:
        """Create a new PR review.
        
        Args:
            pr_review: PR review to create
            
        Returns:
            The created PR review
        """
        return self._save_item(pr_review, "pr_reviews")
    
    def get_pr_review(self, pr_review_id: str) -> Optional[PRReview]:
        """Get a PR review by ID.
        
        Args:
            pr_review_id: ID of the PR review to get
            
        Returns:
            The PR review, or None if not found
        """
        return self._load_item(pr_review_id, "pr_reviews", PRReview)
    
    def get_pr_reviews(self) -> List[PRReview]:
        """Get all PR reviews.
        
        Returns:
            List of PR reviews
        """
        return self._load_items("pr_reviews", PRReview)
    
    def get_pr_reviews_by_number(self, repo: str, pr_number: int) -> List[PRReview]:
        """Get PR reviews by repository and PR number.
        
        Args:
            repo: Repository name
            pr_number: PR number
            
        Returns:
            List of PR reviews
        """
        pr_reviews = self.get_pr_reviews()
        return [pr for pr in pr_reviews if pr.repo == repo and pr.pr_number == pr_number]
    
    def update_pr_review(self, pr_review_id: str, update_data: Dict[str, Any]) -> Optional[PRReview]:
        """Update a PR review.
        
        Args:
            pr_review_id: ID of the PR review to update
            update_data: Data to update
            
        Returns:
            The updated PR review, or None if not found
        """
        pr_review = self.get_pr_review(pr_review_id)
        if not pr_review:
            return None
        
        # Update the PR review
        for key, value in update_data.items():
            if hasattr(pr_review, key):
                setattr(pr_review, key, value)
        
        return self._save_item(pr_review, "pr_reviews")
    
    def delete_pr_review(self, pr_review_id: str) -> bool:
        """Delete a PR review.
        
        Args:
            pr_review_id: ID of the PR review to delete
            
        Returns:
            True if the PR review was deleted, False otherwise
        """
        return self._delete_item(pr_review_id, "pr_reviews")
    
    # Requirement methods
    def create_requirement(self, requirement: Requirement) -> Requirement:
        """Create a new requirement.
        
        Args:
            requirement: Requirement to create
            
        Returns:
            The created requirement
        """
        return self._save_item(requirement, "requirements")
    
    def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """Get a requirement by ID.
        
        Args:
            requirement_id: ID of the requirement to get
            
        Returns:
            The requirement, or None if not found
        """
        return self._load_item(requirement_id, "requirements", Requirement)
    
    def get_requirements(self) -> List[Requirement]:
        """Get all requirements.
        
        Returns:
            List of requirements
        """
        return self._load_items("requirements", Requirement)
    
    def update_requirement(self, requirement_id: str, update_data: Dict[str, Any]) -> Optional[Requirement]:
        """Update a requirement.
        
        Args:
            requirement_id: ID of the requirement to update
            update_data: Data to update
            
        Returns:
            The updated requirement, or None if not found
        """
        requirement = self.get_requirement(requirement_id)
        if not requirement:
            return None
        
        # Update the requirement
        for key, value in update_data.items():
            if hasattr(requirement, key):
                setattr(requirement, key, value)
        
        return self._save_item(requirement, "requirements")
    
    def delete_requirement(self, requirement_id: str) -> bool:
        """Delete a requirement.
        
        Args:
            requirement_id: ID of the requirement to delete
            
        Returns:
            True if the requirement was deleted, False otherwise
        """
        return self._delete_item(requirement_id, "requirements")
    
    # Project Plan methods
    def create_project_plan(self, project_plan: ProjectPlan) -> ProjectPlan:
        """Create a new project plan.
        
        Args:
            project_plan: Project plan to create
            
        Returns:
            The created project plan
        """
        return self._save_item(project_plan, "project_plans")
    
    def get_project_plan(self, project_plan_id: str) -> Optional[ProjectPlan]:
        """Get a project plan by ID.
        
        Args:
            project_plan_id: ID of the project plan to get
            
        Returns:
            The project plan, or None if not found
        """
        return self._load_item(project_plan_id, "project_plans", ProjectPlan)
    
    def get_project_plans(self) -> List[ProjectPlan]:
        """Get all project plans.
        
        Returns:
            List of project plans
        """
        return self._load_items("project_plans", ProjectPlan)
    
    def update_project_plan(self, project_plan_id: str, update_data: Dict[str, Any]) -> Optional[ProjectPlan]:
        """Update a project plan.
        
        Args:
            project_plan_id: ID of the project plan to update
            update_data: Data to update
            
        Returns:
            The updated project plan, or None if not found
        """
        project_plan = self.get_project_plan(project_plan_id)
        if not project_plan:
            return None
        
        # Update the project plan
        for key, value in update_data.items():
            if hasattr(project_plan, key):
                setattr(project_plan, key, value)
        
        return self._save_item(project_plan, "project_plans")
    
    def delete_project_plan(self, project_plan_id: str) -> bool:
        """Delete a project plan.
        
        Args:
            project_plan_id: ID of the project plan to delete
            
        Returns:
            True if the project plan was deleted, False otherwise
        """
        return self._delete_item(project_plan_id, "project_plans")

# Create a singleton instance
db = Database()