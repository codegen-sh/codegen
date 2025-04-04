"""
Simple Codebase class for the PR review bot.
"""

import os
from typing import Dict, Any, Optional, List
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
import logging

logger = logging.getLogger(__name__)

class Codebase:
    """
    A simple Codebase class for GitHub operations.
    """
    
    def __init__(self, repo_name: str, github_token: Optional[str] = None):
        """
        Initialize a Codebase instance.
        
        Args:
            repo_name: The full name of the repository (e.g., "owner/repo")
            github_token: GitHub personal access token
        """
        self.repo_name = repo_name
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        self.github_client = Github(self.github_token)
        self.repo = self.github_client.get_repo(repo_name)
        
    @classmethod
    def from_repo(cls, repo_name: str, language: str = "python", secrets: Dict[str, str] = None):
        """
        Create a Codebase instance from a repository.
        
        Args:
            repo_name: The full name of the repository (e.g., "owner/repo")
            language: The primary language of the repository
            secrets: Dictionary containing secrets like github_token
            
        Returns:
            A Codebase instance
        """
        github_token = None
        if secrets:
            github_token = secrets.get("github_token")
            
        return cls(repo_name, github_token)
    
    def get_pull_request(self, pr_number: int) -> PullRequest:
        """
        Get a pull request by number.
        
        Args:
            pr_number: The pull request number
            
        Returns:
            A GitHub PullRequest object
        """
        return self.repo.get_pull(pr_number)
    
    def create_pr_comment(self, pr_number: int, body: str) -> Any:
        """
        Create a comment on a pull request.
        
        Args:
            pr_number: The pull request number
            body: The comment text
            
        Returns:
            The created comment
        """
        pr = self.get_pull_request(pr_number)
        return pr.create_issue_comment(body)
    
    def create_pr_review_comment(self, pr_number: int, body: str, commit_id: str, path: str, position: int) -> Any:
        """
        Create a review comment on a specific line in a pull request.
        
        Args:
            pr_number: The pull request number
            body: The comment text
            commit_id: The commit SHA
            path: The file path
            position: The position in the diff
            
        Returns:
            The created review comment
        """
        pr = self.get_pull_request(pr_number)
        return pr.create_review_comment(body, commit_id, path, position)
    
    def get_file_content(self, path: str, ref: Optional[str] = None) -> str:
        """
        Get the content of a file.
        
        Args:
            path: The file path
            ref: The reference (branch, tag, or commit)
            
        Returns:
            The file content as a string
        """
        try:
            content_file = self.repo.get_contents(path, ref=ref)
            return content_file.decoded_content.decode('utf-8')
        except Exception as e:
            logger.error(f"Error getting file content: {e}")
            return ""