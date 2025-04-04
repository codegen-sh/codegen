"""
Database module for the integrated agent application.
"""

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

from .models import (
    Document,
    PRReview,
    ProjectPlan,
    Repository,
    Requirement,
    SlackMessage,
)


class JSONDatabase:
    """Simple JSON-based database for storing application data."""

    def __init__(self, data_dir: str):
        """Initialize the database with the data directory."""
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each data type
        self.documents_dir = self.data_dir / "documents"
        self.requirements_dir = self.data_dir / "requirements"
        self.repositories_dir = self.data_dir / "repositories"
        self.pr_reviews_dir = self.data_dir / "pr_reviews"
        self.project_plans_dir = self.data_dir / "project_plans"
        self.slack_messages_dir = self.data_dir / "slack_messages"
        
        # Create subdirectories if they don't exist
        for directory in [
            self.documents_dir,
            self.requirements_dir,
            self.repositories_dir,
            self.pr_reviews_dir,
            self.project_plans_dir,
            self.slack_messages_dir,
        ]:
            directory.mkdir(exist_ok=True)
    
    def _generate_id(self) -> str:
        """Generate a unique ID."""
        return str(uuid.uuid4())
    
    def _save_to_json(self, data: Dict, file_path: Path) -> None:
        """Save data to a JSON file."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    
    def _load_from_json(self, file_path: Path) -> Dict:
        """Load data from a JSON file."""
        if not file_path.exists():
            return {}
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    def _list_files(self, directory: Path) -> List[Path]:
        """List all JSON files in a directory."""
        return list(directory.glob("*.json"))
    
    # Document operations
    
    def create_document(self, document: Document) -> Document:
        """Create a new document."""
        if not document.id:
            document.id = self._generate_id()
        
        document.created_at = datetime.now()
        document.updated_at = datetime.now()
        
        self._save_to_json(
            document.dict(),
            self.documents_dir / f"{document.id}.json",
        )
        
        return document
    
    def get_document(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        file_path = self.documents_dir / f"{document_id}.json"
        if not file_path.exists():
            return None
        
        data = self._load_from_json(file_path)
        return Document(**data)
    
    def update_document(self, document: Document) -> Document:
        """Update a document."""
        existing_document = self.get_document(document.id)
        if not existing_document:
            raise ValueError(f"Document with ID {document.id} not found")
        
        document.created_at = existing_document.created_at
        document.updated_at = datetime.now()
        
        self._save_to_json(
            document.dict(),
            self.documents_dir / f"{document.id}.json",
        )
        
        return document
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        file_path = self.documents_dir / f"{document_id}.json"
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    def list_documents(self) -> List[Document]:
        """List all documents."""
        documents = []
        for file_path in self._list_files(self.documents_dir):
            data = self._load_from_json(file_path)
            documents.append(Document(**data))
        
        return documents
    
    # Requirement operations
    
    def create_requirement(self, requirement: Requirement) -> Requirement:
        """Create a new requirement."""
        if not requirement.id:
            requirement.id = self._generate_id()
        
        requirement.created_at = datetime.now()
        requirement.updated_at = datetime.now()
        
        self._save_to_json(
            requirement.dict(),
            self.requirements_dir / f"{requirement.id}.json",
        )
        
        return requirement
    
    def get_requirement(self, requirement_id: str) -> Optional[Requirement]:
        """Get a requirement by ID."""
        file_path = self.requirements_dir / f"{requirement_id}.json"
        if not file_path.exists():
            return None
        
        data = self._load_from_json(file_path)
        return Requirement(**data)
    
    def update_requirement(self, requirement: Requirement) -> Requirement:
        """Update a requirement."""
        existing_requirement = self.get_requirement(requirement.id)
        if not existing_requirement:
            raise ValueError(f"Requirement with ID {requirement.id} not found")
        
        requirement.created_at = existing_requirement.created_at
        requirement.updated_at = datetime.now()
        
        self._save_to_json(
            requirement.dict(),
            self.requirements_dir / f"{requirement.id}.json",
        )
        
        return requirement
    
    def delete_requirement(self, requirement_id: str) -> bool:
        """Delete a requirement."""
        file_path = self.requirements_dir / f"{requirement_id}.json"
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    def list_requirements(self) -> List[Requirement]:
        """List all requirements."""
        requirements = []
        for file_path in self._list_files(self.requirements_dir):
            data = self._load_from_json(file_path)
            requirements.append(Requirement(**data))
        
        return requirements
    
    # Repository operations
    
    def create_repository(self, repository: Repository) -> Repository:
        """Create a new repository."""
        if not repository.id:
            repository.id = self._generate_id()
        
        repository.created_at = datetime.now()
        repository.updated_at = datetime.now()
        
        self._save_to_json(
            repository.dict(),
            self.repositories_dir / f"{repository.id}.json",
        )
        
        return repository
    
    def get_repository(self, repository_id: str) -> Optional[Repository]:
        """Get a repository by ID."""
        file_path = self.repositories_dir / f"{repository_id}.json"
        if not file_path.exists():
            return None
        
        data = self._load_from_json(file_path)
        return Repository(**data)
    
    def update_repository(self, repository: Repository) -> Repository:
        """Update a repository."""
        existing_repository = self.get_repository(repository.id)
        if not existing_repository:
            raise ValueError(f"Repository with ID {repository.id} not found")
        
        repository.created_at = existing_repository.created_at
        repository.updated_at = datetime.now()
        
        self._save_to_json(
            repository.dict(),
            self.repositories_dir / f"{repository.id}.json",
        )
        
        return repository
    
    def delete_repository(self, repository_id: str) -> bool:
        """Delete a repository."""
        file_path = self.repositories_dir / f"{repository_id}.json"
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    def list_repositories(self) -> List[Repository]:
        """List all repositories."""
        repositories = []
        for file_path in self._list_files(self.repositories_dir):
            data = self._load_from_json(file_path)
            repositories.append(Repository(**data))
        
        return repositories
    
    # PR Review operations
    
    def create_pr_review(self, pr_review: PRReview) -> PRReview:
        """Create a new PR review."""
        file_path = self.pr_reviews_dir / f"{pr_review.repository}_{pr_review.pr_number}.json"
        
        self._save_to_json(
            pr_review.dict(),
            file_path,
        )
        
        return pr_review
    
    def get_pr_review(self, repository: str, pr_number: int) -> Optional[PRReview]:
        """Get a PR review by repository and PR number."""
        file_path = self.pr_reviews_dir / f"{repository}_{pr_number}.json"
        if not file_path.exists():
            return None
        
        data = self._load_from_json(file_path)
        return PRReview(**data)
    
    def update_pr_review(self, pr_review: PRReview) -> PRReview:
        """Update a PR review."""
        file_path = self.pr_reviews_dir / f"{pr_review.repository}_{pr_review.pr_number}.json"
        
        self._save_to_json(
            pr_review.dict(),
            file_path,
        )
        
        return pr_review
    
    def delete_pr_review(self, repository: str, pr_number: int) -> bool:
        """Delete a PR review."""
        file_path = self.pr_reviews_dir / f"{repository}_{pr_number}.json"
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    def list_pr_reviews(self) -> List[PRReview]:
        """List all PR reviews."""
        pr_reviews = []
        for file_path in self._list_files(self.pr_reviews_dir):
            data = self._load_from_json(file_path)
            pr_reviews.append(PRReview(**data))
        
        return pr_reviews
    
    # Project Plan operations
    
    def create_project_plan(self, project_plan: ProjectPlan) -> ProjectPlan:
        """Create a new project plan."""
        if not project_plan.id:
            project_plan.id = self._generate_id()
        
        project_plan.created_at = datetime.now()
        project_plan.updated_at = datetime.now()
        
        self._save_to_json(
            project_plan.dict(),
            self.project_plans_dir / f"{project_plan.id}.json",
        )
        
        return project_plan
    
    def get_project_plan(self, project_plan_id: str) -> Optional[ProjectPlan]:
        """Get a project plan by ID."""
        file_path = self.project_plans_dir / f"{project_plan_id}.json"
        if not file_path.exists():
            return None
        
        data = self._load_from_json(file_path)
        return ProjectPlan(**data)
    
    def update_project_plan(self, project_plan: ProjectPlan) -> ProjectPlan:
        """Update a project plan."""
        existing_project_plan = self.get_project_plan(project_plan.id)
        if not existing_project_plan:
            raise ValueError(f"Project plan with ID {project_plan.id} not found")
        
        project_plan.created_at = existing_project_plan.created_at
        project_plan.updated_at = datetime.now()
        
        self._save_to_json(
            project_plan.dict(),
            self.project_plans_dir / f"{project_plan.id}.json",
        )
        
        return project_plan
    
    def delete_project_plan(self, project_plan_id: str) -> bool:
        """Delete a project plan."""
        file_path = self.project_plans_dir / f"{project_plan_id}.json"
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    def list_project_plans(self) -> List[ProjectPlan]:
        """List all project plans."""
        project_plans = []
        for file_path in self._list_files(self.project_plans_dir):
            data = self._load_from_json(file_path)
            project_plans.append(ProjectPlan(**data))
        
        return project_plans
    
    # Slack Message operations
    
    def create_slack_message(self, slack_message: SlackMessage) -> SlackMessage:
        """Create a new slack message."""
        if not slack_message.id:
            slack_message.id = self._generate_id()
        
        self._save_to_json(
            slack_message.dict(),
            self.slack_messages_dir / f"{slack_message.id}.json",
        )
        
        return slack_message
    
    def get_slack_message(self, slack_message_id: str) -> Optional[SlackMessage]:
        """Get a slack message by ID."""
        file_path = self.slack_messages_dir / f"{slack_message_id}.json"
        if not file_path.exists():
            return None
        
        data = self._load_from_json(file_path)
        return SlackMessage(**data)
    
    def delete_slack_message(self, slack_message_id: str) -> bool:
        """Delete a slack message."""
        file_path = self.slack_messages_dir / f"{slack_message_id}.json"
        if not file_path.exists():
            return False
        
        file_path.unlink()
        return True
    
    def list_slack_messages(self) -> List[SlackMessage]:
        """List all slack messages."""
        slack_messages = []
        for file_path in self._list_files(self.slack_messages_dir):
            data = self._load_from_json(file_path)
            slack_messages.append(SlackMessage(**data))
        
        return slack_messages