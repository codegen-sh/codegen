"""
Database module for the unified agent application.
This module provides a JSON-based database for storing application data.
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, TypeVar, Generic, Type
import threading

from .models import (
    BaseItem, Settings, Workflow, WorkflowStep, PRReview, 
    Requirement, ProjectPlan, WorkflowStatus, StepStatus
)
from .config import config

T = TypeVar('T', bound=BaseItem)

class JSONDatabase:
    """JSON-based database for storing application data."""
    
    def __init__(self, data_dir: str = None):
        """Initialize the database."""
        self.data_dir = data_dir or config.app.data_dir
        self.settings_file = os.path.join(self.data_dir, "settings.json")
        self.workflows_file = os.path.join(self.data_dir, "workflows.json")
        self.pr_reviews_file = os.path.join(self.data_dir, "pr_reviews.json")
        self.requirements_file = os.path.join(self.data_dir, "requirements.json")
        self.project_plans_file = os.path.join(self.data_dir, "project_plans.json")
        
        self.settings = Settings()
        self.workflows: Dict[str, Workflow] = {}
        self.pr_reviews: Dict[str, PRReview] = {}
        self.requirements: Dict[str, Requirement] = {}
        self.project_plans: Dict[str, ProjectPlan] = {}
        
        self.lock = threading.RLock()
        
        self._ensure_data_dir()
        self._load_data()
    
    def _ensure_data_dir(self) -> None:
        """Ensure the data directory exists."""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _load_data(self) -> None:
        """Load data from files."""
        with self.lock:
            # Load settings
            if os.path.exists(self.settings_file):
                try:
                    with open(self.settings_file, "r") as f:
                        self.settings = Settings(**json.load(f))
                except (json.JSONDecodeError, KeyError):
                    self.settings = Settings()
            
            # Load workflows
            if os.path.exists(self.workflows_file):
                try:
                    with open(self.workflows_file, "r") as f:
                        workflows_data = json.load(f)
                        self.workflows = {
                            id: Workflow(**data) for id, data in workflows_data.items()
                        }
                except (json.JSONDecodeError, KeyError):
                    self.workflows = {}
            
            # Load PR reviews
            if os.path.exists(self.pr_reviews_file):
                try:
                    with open(self.pr_reviews_file, "r") as f:
                        pr_reviews_data = json.load(f)
                        self.pr_reviews = {
                            id: PRReview(**data) for id, data in pr_reviews_data.items()
                        }
                except (json.JSONDecodeError, KeyError):
                    self.pr_reviews = {}
            
            # Load requirements
            if os.path.exists(self.requirements_file):
                try:
                    with open(self.requirements_file, "r") as f:
                        requirements_data = json.load(f)
                        self.requirements = {
                            id: Requirement(**data) for id, data in requirements_data.items()
                        }
                except (json.JSONDecodeError, KeyError):
                    self.requirements = {}
            
            # Load project plans
            if os.path.exists(self.project_plans_file):
                try:
                    with open(self.project_plans_file, "r") as f:
                        project_plans_data = json.load(f)
                        self.project_plans = {
                            id: ProjectPlan(**data) for id, data in project_plans_data.items()
                        }
                except (json.JSONDecodeError, KeyError):
                    self.project_plans = {}
    
    def _save_data(self) -> None:
        """Save data to files."""
        with self.lock:
            # Save settings
            with open(self.settings_file, "w") as f:
                json.dump(self.settings.dict(), f, default=self._json_serializer)
            
            # Save workflows
            with open(self.workflows_file, "w") as f:
                workflows_data = {
                    id: workflow.dict() for id, workflow in self.workflows.items()
                }
                json.dump(workflows_data, f, default=self._json_serializer)
            
            # Save PR reviews
            with open(self.pr_reviews_file, "w") as f:
                pr_reviews_data = {
                    id: pr_review.dict() for id, pr_review in self.pr_reviews.items()
                }
                json.dump(pr_reviews_data, f, default=self._json_serializer)
            
            # Save requirements
            with open(self.requirements_file, "w") as f:
                requirements_data = {
                    id: requirement.dict() for id, requirement in self.requirements.items()
                }
                json.dump(requirements_data, f, default=self._json_serializer)
            
            # Save project plans
            with open(self.project_plans_file, "w") as f:
                project_plans_data = {
                    id: project_plan.dict() for id, project_plan in self.project_plans.items()
                }
                json.dump(project_plans_data, f, default=self._json_serializer)
    
    def _json_serializer(self, obj: Any) -> Any:
        """JSON serializer for objects not serializable by default json code."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, (WorkflowStatus, StepStatus)):
            return obj.value
        raise TypeError(f"Type {type(obj)} not serializable")
    
    def get_settings(self) -> Settings:
        """Get the application settings."""
        with self.lock:
            return self.settings
    
    def update_settings(self, settings: Settings) -> Settings:
        """Update the application settings."""
        with self.lock:
            self.settings = settings
            self._save_data()
            return self.settings
    
    def create_workflow(self, workflow: Workflow) -> Workflow:
        """Create a new workflow."""
        with self.lock:
            workflow_id = str(uuid.uuid4())
            workflow.id = workflow_id
            workflow.created_at = datetime.now()
            workflow.updated_at = datetime.now()
            self.workflows[workflow_id] = workflow
            self._save_data()
            return workflow
    
    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get a workflow by ID."""
        with self.lock:
            return self.workflows.get(workflow_id)
    
    def get_workflows(self, workflow_type: Optional[str] = None) -> List[Workflow]:
        """Get all workflows, optionally filtered by type."""
        with self.lock:
            if workflow_type:
                return [w for w in self.workflows.values() if w.type == workflow_type]
            return list(self.workflows.values())
    
    def update_workflow(self, workflow_id: str, workflow_update: Dict[str, Any]) -> Optional[Workflow]:
        """Update a workflow."""
        with self.lock:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return None
            
            for key, value in workflow_update.items():
                if hasattr(workflow, key):
                    setattr(workflow, key, value)
            
            workflow.updated_at = datetime.now()
            self._save_data()
            return workflow
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow."""
        with self.lock:
            if workflow_id in self.workflows:
                del self.workflows[workflow_id]
                self._save_data()
                return True
            return False
    
    def update_workflow_step(self, workflow_id: str, step_id: str, step_update: Dict[str, Any]) -> Optional[Workflow]:
        """Update a workflow step."""
        with self.lock:
            workflow = self.workflows.get(workflow_id)
            if not workflow:
                return None
            
            for i, step in enumerate(workflow.steps):
                if step.id == step_id:
                    for key, value in step_update.items():
                        if hasattr(step, key):
                            setattr(step, key, value)
                    
                    workflow.updated_at = datetime.now()
                    self._save_data()
                    return workflow
            
            return None
    
    def create_pr_review(self, pr_review: PRReview) -> PRReview:
        """Create a new PR review."""
        with self.lock:
            pr_review_id = str(uuid.uuid4())
            pr_review.id = pr_review_id
            pr_review.created_at = datetime.now()
            pr_review.updated_at = datetime.now()
            self.pr_reviews[pr_review_id] = pr_review
            self._save_data()
            return pr_review
    
    def get_pr_review(self, pr_review_id: str) -> Optional[PRReview]:
        """Get a PR review by ID."""
        with self.lock:
            return self.pr_reviews.get(pr_review_id)
    
    def get_pr_reviews(self) -> List[PRReview]:
        """Get all PR reviews."""
        with self.lock:
            return list(self.pr_reviews.values())
    
    def update_pr_review(self, pr_review_id: str, pr_review_update: Dict[str, Any]) -> Optional[PRReview]:
        """Update a PR review."""
        with self.lock:
            pr_review = self.pr_reviews.get(pr_review_id)
            if not pr_review:
                return None
            
            for key, value in pr_review_update.items():
                if hasattr(pr_review, key):
                    setattr(pr_review, key, value)
            
            pr_review.updated_at = datetime.now()
            self._save_data()
            return pr_review
    
    def delete_pr_review(self, pr_review_id: str) -> bool:
        """Delete a PR review."""
        with self.lock:
            if pr_review_id in self.pr_reviews:
                del self.pr_reviews[pr_review_id]
                self._save_data()
                return True
            return False
    
    def create_requirement(self, requirement: Requirement) -> Requirement:
        """Create a new requirement."""
        with self.lock:
            requirement_id = str(uuid.uuid4())
            requirement.id = requirement_id
            requirement.created_at = datetime.now()
            requirement.updated_at = datetime.now()
            self.requirements[requirement_id] = requirement
            self._save_data()
            return requirement
    
    def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """Get a requirement by ID."""
        with self.lock:
            return self.requirements.get(requirement_id)
    
    def get_requirements(self) -> List[Requirement]:
        """Get all requirements."""
        with self.lock:
            return list(self.requirements.values())
    
    def update_requirement(self, requirement_id: str, requirement_update: Dict[str, Any]) -> Optional[Requirement]:
        """Update a requirement."""
        with self.lock:
            requirement = self.requirements.get(requirement_id)
            if not requirement:
                return None
            
            for key, value in requirement_update.items():
                if hasattr(requirement, key):
                    setattr(requirement, key, value)
            
            requirement.updated_at = datetime.now()
            self._save_data()
            return requirement
    
    def delete_requirement(self, requirement_id: str) -> bool:
        """Delete a requirement."""
        with self.lock:
            if requirement_id in self.requirements:
                del self.requirements[requirement_id]
                self._save_data()
                return True
            return False
    
    def create_project_plan(self, project_plan: ProjectPlan) -> ProjectPlan:
        """Create a new project plan."""
        with self.lock:
            project_plan_id = str(uuid.uuid4())
            project_plan.id = project_plan_id
            project_plan.created_at = datetime.now()
            project_plan.updated_at = datetime.now()
            self.project_plans[project_plan_id] = project_plan
            self._save_data()
            return project_plan
    
    def get_project_plan(self, project_plan_id: str) -> Optional[ProjectPlan]:
        """Get a project plan by ID."""
        with self.lock:
            return self.project_plans.get(project_plan_id)
    
    def get_project_plans(self) -> List[ProjectPlan]:
        """Get all project plans."""
        with self.lock:
            return list(self.project_plans.values())
    
    def update_project_plan(self, project_plan_id: str, project_plan_update: Dict[str, Any]) -> Optional[ProjectPlan]:
        """Update a project plan."""
        with self.lock:
            project_plan = self.project_plans.get(project_plan_id)
            if not project_plan:
                return None
            
            for key, value in project_plan_update.items():
                if hasattr(project_plan, key):
                    setattr(project_plan, key, value)
            
            project_plan.updated_at = datetime.now()
            self._save_data()
            return project_plan
    
    def delete_project_plan(self, project_plan_id: str) -> bool:
        """Delete a project plan."""
        with self.lock:
            if project_plan_id in self.project_plans:
                del self.project_plans[project_plan_id]
                self._save_data()
                return True
            return False

# Global database instance
db = JSONDatabase()