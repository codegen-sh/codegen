"""
Codegen integration module for the Project Plan Manager.
This module provides integration with Codegen features for code context and GitHub management.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union

from codegen import Codebase
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.sdk.codebase.config import ProjectConfig

from .config import config
from .models import Workflow, WorkflowStep, WorkflowStatus, StepStatus

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CodegenIntegration:
    """Integration with Codegen features for the Project Plan Manager."""
    
    def __init__(self):
        """Initialize the Codegen integration."""
        self.github_token = config.github.token
        self.repos_dir = os.path.join(config.app.output_dir, "repos")
        
        # Ensure repos directory exists
        os.makedirs(self.repos_dir, exist_ok=True)
        
        # Initialize repo operator and codebase instances
        self.repo_operators = {}
        self.codebases = {}
    
    def get_repo_operator(self, repo_name: str) -> RepoOperator:
        """Get or create a RepoOperator for the specified repository.
        
        Args:
            repo_name: The name of the repository (format: owner/repo)
            
        Returns:
            RepoOperator instance for the repository
        """
        if repo_name not in self.repo_operators:
            # Parse owner and repo from repo_name
            owner, repo = repo_name.split('/')
            
            # Create repo config
            repo_config = RepoConfig(
                owner=owner,
                name=repo,
                token=self.github_token,
                branch="main"  # Default to main, can be updated later
            )
            
            # Create repo operator
            repo_path = os.path.join(self.repos_dir, repo)
            self.repo_operators[repo_name] = RepoOperator(
                repo_config=repo_config,
                repo_path=repo_path
            )
            
            # Clone the repository if it doesn't exist
            if not os.path.exists(repo_path):
                logger.info(f"Cloning repository {repo_name} to {repo_path}")
                self.repo_operators[repo_name].clone()
            else:
                logger.info(f"Repository {repo_name} already exists at {repo_path}")
                self.repo_operators[repo_name].pull()
        
        return self.repo_operators[repo_name]
    
    def get_codebase(self, repo_name: str) -> Codebase:
        """Get or create a Codebase for the specified repository.
        
        Args:
            repo_name: The name of the repository (format: owner/repo)
            
        Returns:
            Codebase instance for the repository
        """
        if repo_name not in self.codebases:
            # Get repo operator
            repo_operator = self.get_repo_operator(repo_name)
            
            # Create project config
            project_config = ProjectConfig(
                root_path=repo_operator.repo_path,
                include_patterns=["**/*"],
                exclude_patterns=["**/node_modules/**", "**/.git/**"]
            )
            
            # Create codebase
            self.codebases[repo_name] = Codebase(project_config)
        
        return self.codebases[repo_name]
    
    def search_code(self, repo_name: str, query: str) -> List[Dict[str, Any]]:
        """Search for code in the repository.
        
        Args:
            repo_name: The name of the repository (format: owner/repo)
            query: The search query
            
        Returns:
            List of search results
        """
        codebase = self.get_codebase(repo_name)
        results = codebase.search(query)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_results.append({
                "file_path": result.file_path,
                "line_number": result.line_number,
                "line": result.line,
                "context": result.context
            })
        
        return formatted_results
    
    def get_file_content(self, repo_name: str, file_path: str) -> str:
        """Get the content of a file in the repository.
        
        Args:
            repo_name: The name of the repository (format: owner/repo)
            file_path: The path to the file
            
        Returns:
            The content of the file
        """
        codebase = self.get_codebase(repo_name)
        return codebase.get_file_content(file_path)
    
    def create_pr(self, repo_name: str, title: str, body: str, 
                 base_branch: str = "main", head_branch: str = None) -> Dict[str, Any]:
        """Create a pull request in the repository.
        
        Args:
            repo_name: The name of the repository (format: owner/repo)
            title: The title of the PR
            body: The body of the PR
            base_branch: The base branch for the PR
            head_branch: The head branch for the PR
            
        Returns:
            Dictionary with PR details
        """
        repo_operator = self.get_repo_operator(repo_name)
        
        # Create a new branch if head_branch is not provided
        if head_branch is None:
            import uuid
            head_branch = f"codegen-pr-{uuid.uuid4().hex[:8]}"
            repo_operator.create_branch(head_branch)
        
        # Create PR
        pr = repo_operator.create_pr(
            title=title,
            body=body,
            base_branch=base_branch,
            head_branch=head_branch
        )
        
        return {
            "pr_number": pr.number,
            "pr_url": pr.html_url,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state
        }
    
    def get_pr_details(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Get details of a pull request.
        
        Args:
            repo_name: The name of the repository (format: owner/repo)
            pr_number: The PR number
            
        Returns:
            Dictionary with PR details
        """
        repo_operator = self.get_repo_operator(repo_name)
        pr = repo_operator.get_pr(pr_number)
        
        return {
            "pr_number": pr.number,
            "pr_url": pr.html_url,
            "title": pr.title,
            "body": pr.body,
            "state": pr.state,
            "user": pr.user.login,
            "created_at": pr.created_at.isoformat(),
            "updated_at": pr.updated_at.isoformat(),
            "merged": pr.merged,
            "mergeable": pr.mergeable,
            "mergeable_state": pr.mergeable_state,
            "comments": pr.comments,
            "commits": pr.commits,
            "additions": pr.additions,
            "deletions": pr.deletions,
            "changed_files": pr.changed_files
        }

# Create a singleton instance
codegen_integration = CodegenIntegration()