"""
Simple Codebase class for GitHub operations.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from github import Github
from github.Repository import Repository

logger = logging.getLogger("pr_review_bot")

class Codebase:
    """
    Simple Codebase class for GitHub operations.
    This is a lightweight version that doesn't require the full codegen package.
    """
    
    def __init__(self, repo_name: str, github_token: Optional[str] = None):
        """
        Initialize a Codebase instance.
        
        Args:
            repo_name: Repository name in the format "owner/repo"
            github_token: GitHub token (defaults to GITHUB_TOKEN environment variable)
        """
        self.repo_name = repo_name
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        # Initialize GitHub client
        self.github = Github(self.github_token)
        
        # Get repository
        try:
            self.repo = self.github.get_repo(repo_name)
            logger.info(f"Initialized Codebase for {repo_name}")
        except Exception as e:
            logger.error(f"Error initializing Codebase for {repo_name}: {e}")
            raise
    
    def get_file_content(self, path: str, ref: Optional[str] = None) -> str:
        """
        Get the content of a file.
        
        Args:
            path: File path
            ref: Git reference (branch, tag, commit)
            
        Returns:
            File content as string
        """
        try:
            content = self.repo.get_contents(path, ref=ref)
            return content.decoded_content.decode("utf-8")
        except Exception as e:
            logger.error(f"Error getting file content for {path}: {e}")
            raise
    
    def list_directory(self, path: str, ref: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List the contents of a directory.
        
        Args:
            path: Directory path
            ref: Git reference (branch, tag, commit)
            
        Returns:
            List of directory contents
        """
        try:
            contents = self.repo.get_contents(path, ref=ref)
            
            # Handle single file case
            if not isinstance(contents, list):
                contents = [contents]
            
            return [
                {
                    "name": content.name,
                    "path": content.path,
                    "type": "file" if content.type == "file" else "directory",
                    "size": content.size if content.type == "file" else 0,
                }
                for content in contents
            ]
        except Exception as e:
            logger.error(f"Error listing directory {path}: {e}")
            raise
    
    def search_code(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for code in the repository.
        
        Args:
            query: Search query
            
        Returns:
            List of search results
        """
        try:
            # Add repo filter to query
            repo_query = f"repo:{self.repo_name} {query}"
            
            # Search code
            results = self.github.search_code(repo_query)
            
            return [
                {
                    "name": result.name,
                    "path": result.path,
                    "url": result.html_url,
                    "repository": result.repository.full_name,
                }
                for result in results
            ]
        except Exception as e:
            logger.error(f"Error searching code with query '{query}': {e}")
            raise
    
    def get_pull_request(self, pr_number: int) -> Dict[str, Any]:
        """
        Get a pull request.
        
        Args:
            pr_number: Pull request number
            
        Returns:
            Pull request details
        """
        try:
            pr = self.repo.get_pull(pr_number)
            
            return {
                "number": pr.number,
                "title": pr.title,
                "body": pr.body,
                "state": pr.state,
                "user": pr.user.login,
                "created_at": pr.created_at.isoformat(),
                "updated_at": pr.updated_at.isoformat(),
                "head": pr.head.ref,
                "base": pr.base.ref,
                "mergeable": pr.mergeable,
            }
        except Exception as e:
            logger.error(f"Error getting PR #{pr_number}: {e}")
            raise
    
    def create_pr_comment(self, pr_number: int, body: str) -> Dict[str, Any]:
        """
        Create a comment on a pull request.
        
        Args:
            pr_number: Pull request number
            body: Comment body
            
        Returns:
            Comment details
        """
        try:
            pr = self.repo.get_pull(pr_number)
            comment = pr.create_issue_comment(body)
            
            return {
                "id": comment.id,
                "body": comment.body,
                "user": comment.user.login,
                "created_at": comment.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error creating comment on PR #{pr_number}: {e}")
            raise
    
    def create_pr_review_comment(self, pr_number: int, body: str, commit_id: str, path: str, position: int) -> Dict[str, Any]:
        """
        Create a review comment on a pull request.
        
        Args:
            pr_number: Pull request number
            body: Comment body
            commit_id: Commit ID
            path: File path
            position: Line position
            
        Returns:
            Comment details
        """
        try:
            pr = self.repo.get_pull(pr_number)
            comment = pr.create_review_comment(body, commit_id, path, position)
            
            return {
                "id": comment.id,
                "body": comment.body,
                "user": comment.user.login,
                "created_at": comment.created_at.isoformat(),
            }
        except Exception as e:
            logger.error(f"Error creating review comment on PR #{pr_number}: {e}")
            raise