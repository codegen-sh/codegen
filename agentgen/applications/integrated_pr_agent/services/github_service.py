"""
GitHub service for interacting with GitHub repositories.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Union, Any

import github
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest as GithubPR

from ..models import PullRequest, PRStatus, PRReviewStatus, PRSuggestion

logger = logging.getLogger("integrated_pr_agent")


class GitHubService:
    """Service for interacting with GitHub repositories."""
    
    def __init__(self, github_token: Optional[str] = None):
        """Initialize the GitHub service."""
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        self.github = Github(self.github_token)
    
    def get_repository(self, repo_name: str) -> Repository:
        """Get a GitHub repository."""
        return self.github.get_repo(repo_name)
    
    def get_pull_request(self, repo_name: str, pr_number: int) -> GithubPR:
        """Get a GitHub pull request."""
        repo = self.get_repository(repo_name)
        return repo.get_pull(pr_number)
    
    def convert_to_model(self, github_pr: GithubPR) -> PullRequest:
        """Convert a GitHub PR to our model."""
        # Determine PR status
        if github_pr.merged:
            status = PRStatus.MERGED
        elif github_pr.state == "closed":
            status = PRStatus.CLOSED
        else:
            status = PRStatus.OPEN
        
        # Create PullRequest model
        return PullRequest(
            number=github_pr.number,
            title=github_pr.title,
            body=github_pr.body,
            status=status,
            created_at=github_pr.created_at,
            updated_at=github_pr.updated_at,
            author=github_pr.user.login,
            repository=github_pr.base.repo.full_name,
            base_branch=github_pr.base.ref,
            head_branch=github_pr.head.ref,
        )
    
    def get_pull_request_model(self, repo_name: str, pr_number: int) -> PullRequest:
        """Get a pull request as our model."""
        github_pr = self.get_pull_request(repo_name, pr_number)
        return self.convert_to_model(github_pr)
    
    def get_pull_requests(self, repo_name: str, state: str = "open") -> List[PullRequest]:
        """Get all pull requests for a repository."""
        repo = self.get_repository(repo_name)
        github_prs = repo.get_pulls(state=state)
        
        return [self.convert_to_model(pr) for pr in github_prs]
    
    def create_pr_comment(self, repo_name: str, pr_number: int, body: str) -> Dict[str, Any]:
        """Create a comment on a pull request."""
        github_pr = self.get_pull_request(repo_name, pr_number)
        comment = github_pr.create_issue_comment(body)
        
        return {
            "id": comment.id,
            "body": comment.body,
            "user": comment.user.login,
            "created_at": comment.created_at.isoformat(),
        }
    
    def create_pr_review(self, repo_name: str, pr_number: int, body: str, event: str) -> Dict[str, Any]:
        """Create a review on a pull request."""
        github_pr = self.get_pull_request(repo_name, pr_number)
        review = github_pr.create_review(body=body, event=event)
        
        return {
            "id": review.id,
            "body": review.body,
            "user": review.user.login,
            "state": review.state,
            "submitted_at": review.submitted_at.isoformat() if review.submitted_at else None,
        }
    
    def create_pr_review_comment(
        self, repo_name: str, pr_number: int, body: str, commit_id: str, path: str, position: int
    ) -> Dict[str, Any]:
        """Create a review comment on a pull request."""
        github_pr = self.get_pull_request(repo_name, pr_number)
        comment = github_pr.create_review_comment(body=body, commit_id=commit_id, path=path, position=position)
        
        return {
            "id": comment.id,
            "body": comment.body,
            "user": comment.user.login,
            "created_at": comment.created_at.isoformat(),
        }
    
    def get_file_content(self, repo_name: str, path: str, ref: Optional[str] = None) -> str:
        """Get the content of a file."""
        repo = self.get_repository(repo_name)
        content = repo.get_contents(path, ref=ref)
        return content.decoded_content.decode("utf-8")
    
    def search_code(self, query: str, repo_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for code in GitHub."""
        if repo_name:
            query = f"repo:{repo_name} {query}"
        
        results = self.github.search_code(query)
        
        return [
            {
                "name": result.name,
                "path": result.path,
                "url": result.html_url,
                "repository": result.repository.full_name,
            }
            for result in results
        ]