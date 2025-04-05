"""
PR Review Agent Integration for Project Plan Manager.
This module integrates the PR Review Agent with the Project Plan Manager.
"""

import os
import logging
import hmac
import hashlib
import json
from typing import Dict, List, Any, Optional, Union

from agentgen.agents.pr_review.agent import PRReviewAgent
from agentgen.agents.utils import AgentConfig
from agentgen.shared.logging.get_logger import get_logger
from ..models import PRReview, PRReviewStatus, PRReviewComment
from ..database import db
from ..config import config

logger = get_logger(__name__)

class PRReviewAgentIntegration:
    """Integration of PR Review Agent with Project Plan Manager."""
    
    def __init__(self):
        """Initialize the PR Review Agent Integration."""
        self.github_token = config.github.token
        self.slack_token = config.slack.bot_token
        self.slack_channel_id = config.slack.channel_id
        self.output_dir = config.app.output_dir
        self.webhook_secret = config.github.webhook_secret
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
    
    def review_pr(self, pr_review: PRReview) -> Dict[str, Any]:
        """Review a PR using the PR Review Agent.
        
        Args:
            pr_review: The PR review object
            
        Returns:
            Dictionary with review results
        """
        logger.info(f"Reviewing PR #{pr_review.pr_number} in {pr_review.repo}")
        
        try:
            # Create a codebase object for the repository
            from agentgen.codebase.github_codebase import GitHubCodebase
            
            codebase = GitHubCodebase(
                repo=pr_review.repo,
                github_token=self.github_token,
                cache_dir=os.path.join(self.output_dir, "codebase_cache")
            )
            
            # Create the PR Review Agent
            agent = PRReviewAgent(
                codebase=codebase,
                github_token=self.github_token,
                slack_token=self.slack_token,
                slack_channel_id=self.slack_channel_id,
                output_dir=self.output_dir,
                model_provider=config.ai.provider,
                model_name=config.ai.model_name,
                memory=True
            )
            
            # Review the PR
            review_result = agent.review_pr(
                repo_name=pr_review.repo,
                pr_number=pr_review.pr_number
            )
            
            # Update the PR review with the results
            comments = []
            for issue in review_result.get("issues", []):
                comments.append(
                    PRReviewComment(
                        id=os.urandom(16).hex(),
                        body=issue,
                        file=None,
                        line=None
                    )
                )
            
            for suggestion in review_result.get("suggestions", []):
                if isinstance(suggestion, dict):
                    comments.append(
                        PRReviewComment(
                            id=os.urandom(16).hex(),
                            body=suggestion.get("description", ""),
                            file=suggestion.get("file_path"),
                            line=suggestion.get("line_number")
                        )
                    )
                else:
                    comments.append(
                        PRReviewComment(
                            id=os.urandom(16).hex(),
                            body=suggestion,
                            file=None,
                            line=None
                        )
                    )
            
            # Add the detailed review comment
            if review_result.get("review_comment"):
                comments.append(
                    PRReviewComment(
                        id=os.urandom(16).hex(),
                        body=review_result.get("review_comment"),
                        file=None,
                        line=None
                    )
                )
            
            # Update the PR review status
            status = PRReviewStatus.COMPLETED
            if not review_result.get("compliant", False):
                status = PRReviewStatus.FAILED
            
            # Update the PR review in the database
            db.update_pr_review(
                pr_review.id,
                {
                    "status": status,
                    "comments": comments,
                    "metadata": {
                        **pr_review.metadata,
                        "review_result": review_result
                    }
                }
            )
            
            return review_result
        
        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            
            # Update the PR review status to failed
            db.update_pr_review(
                pr_review.id,
                {
                    "status": PRReviewStatus.FAILED,
                    "metadata": {
                        **pr_review.metadata,
                        "error": str(e)
                    }
                }
            )
            
            return {
                "pr_number": pr_review.pr_number,
                "repo_name": pr_review.repo,
                "compliant": False,
                "approval_recommendation": "request_changes",
                "issues": [f"Error during review: {str(e)}"],
                "suggestions": ["Please review manually"],
                "error": str(e)
            }
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify the GitHub webhook signature.
        
        Args:
            payload: The webhook payload
            signature: The X-Hub-Signature-256 header value
            
        Returns:
            True if the signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("No webhook secret configured - skipping signature verification")
            return True
        
        if not signature:
            logger.warning("No X-Hub-Signature-256 header provided - skipping verification")
            return True
        
        computed_signature = "sha256=" + hmac.new(
            self.webhook_secret.encode(),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_signature, signature)
    
    def handle_webhook(self, event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a GitHub webhook event.
        
        Args:
            event_type: The GitHub event type
            payload: The webhook payload
            
        Returns:
            Optional response data
        """
        logger.info(f"Handling GitHub webhook event: {event_type}")
        
        if event_type == "pull_request":
            return self._handle_pull_request_event(payload)
        elif event_type == "issue_comment":
            return self._handle_issue_comment_event(payload)
        
        logger.info(f"Ignoring unsupported event type: {event_type}")
        return None
    
    def _handle_pull_request_event(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle a pull_request event.
        
        Args:
            payload: The webhook payload
            
        Returns:
            Optional response data
        """
        action = payload.get("action")
        pr = payload.get("pull_request", {})
        repo = payload.get("repository", {})
        
        if not pr or not repo:
            logger.warning("Invalid pull_request payload")
            return None
        
        pr_number = pr.get("number")
        repo_name = repo.get("full_name")
        
        if not pr_number or not repo_name:
            logger.warning("Missing PR number or repo name in payload")
            return None
        
        logger.info(f"Handling pull_request event: {action} for PR #{pr_number} in {repo_name}")
        
        # Only process opened or synchronize events if auto-review is enabled
        if action in ["opened", "synchronize"] and config.workflow.auto_review_prs:
            # Check if we already have a review for this PR
            existing_reviews = db.get_pr_reviews_by_number(repo_name, pr_number)
            
            if existing_reviews:
                # Update the existing review
                pr_review = existing_reviews[0]
                db.update_pr_review(
                    pr_review.id,
                    {
                        "status": PRReviewStatus.PENDING,
                        "metadata": {
                            **pr_review.metadata,
                            "updated_at": pr.get("updated_at"),
                            "action": action
                        }
                    }
                )
                logger.info(f"Updated existing PR review for PR #{pr_number} in {repo_name}")
            else:
                # Create a new PR review
                from ..models import PRReviewCreate
                
                pr_review_create = PRReviewCreate(
                    pr_number=pr_number,
                    repo=repo_name,
                    title=pr.get("title", f"PR #{pr_number}"),
                    description=pr.get("body", ""),
                    metadata={
                        "created_at": pr.get("created_at"),
                        "updated_at": pr.get("updated_at"),
                        "action": action,
                        "user": pr.get("user", {}).get("login"),
                        "html_url": pr.get("html_url")
                    }
                )
                
                from ..api import create_pr_review
                pr_review = create_pr_review(pr_review_create)
                logger.info(f"Created new PR review for PR #{pr_number} in {repo_name}")
            
            return {"pr_review_id": pr_review.id}
        
        return None
    
    def _handle_issue_comment_event(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle an issue_comment event.
        
        Args:
            payload: The webhook payload
            
        Returns:
            Optional response data
        """
        action = payload.get("action")
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})
        repo = payload.get("repository", {})
        
        if not comment or not issue or not repo:
            logger.warning("Invalid issue_comment payload")
            return None
        
        # Only process if this is a PR comment (issues with pull_request field)
        if "pull_request" not in issue:
            logger.info("Ignoring comment on regular issue (not a PR)")
            return None
        
        pr_number = issue.get("number")
        repo_name = repo.get("full_name")
        comment_body = comment.get("body", "")
        
        if not pr_number or not repo_name:
            logger.warning("Missing PR number or repo name in payload")
            return None
        
        logger.info(f"Handling issue_comment event: {action} for PR #{pr_number} in {repo_name}")
        
        # Check if the comment is requesting a review
        review_triggers = [
            "@codegen review",
            "@codegen please review",
            "codegen review",
            "codegen please review"
        ]
        
        if action == "created" and any(trigger.lower() in comment_body.lower() for trigger in review_triggers):
            # Check if we already have a review for this PR
            existing_reviews = db.get_pr_reviews_by_number(repo_name, pr_number)
            
            if existing_reviews:
                # Update the existing review
                pr_review = existing_reviews[0]
                db.update_pr_review(
                    pr_review.id,
                    {
                        "status": PRReviewStatus.PENDING,
                        "metadata": {
                            **pr_review.metadata,
                            "comment_id": comment.get("id"),
                            "comment_user": comment.get("user", {}).get("login"),
                            "comment_body": comment_body
                        }
                    }
                )
                logger.info(f"Updated existing PR review for PR #{pr_number} in {repo_name} based on comment")
            else:
                # Create a new PR review
                from ..models import PRReviewCreate
                
                pr_review_create = PRReviewCreate(
                    pr_number=pr_number,
                    repo=repo_name,
                    title=issue.get("title", f"PR #{pr_number}"),
                    description=issue.get("body", ""),
                    metadata={
                        "comment_id": comment.get("id"),
                        "comment_user": comment.get("user", {}).get("login"),
                        "comment_body": comment_body,
                        "html_url": issue.get("html_url")
                    }
                )
                
                from ..api import create_pr_review
                pr_review = create_pr_review(pr_review_create)
                logger.info(f"Created new PR review for PR #{pr_number} in {repo_name} based on comment")
            
            return {"pr_review_id": pr_review.id}
        
        return None
    
    def post_review_to_github(self, pr_review: PRReview) -> Dict[str, Any]:
        """Post a review to GitHub.
        
        Args:
            pr_review: The PR review object
            
        Returns:
            Dictionary with the result of the GitHub API call
        """
        try:
            from github import Github
            
            # Create a GitHub client
            github_client = Github(self.github_token)
            
            # Get the repository and PR
            repo = github_client.get_repo(pr_review.repo)
            pr = repo.get_pull(pr_review.pr_number)
            
            # Prepare the review comments
            review_comments = []
            for comment in pr_review.comments:
                if comment.file and comment.line:
                    # This is a line comment
                    review_comments.append({
                        "path": comment.file,
                        "line": comment.line,
                        "body": comment.body
                    })
            
            # Prepare the review body
            review_body = f"# PR Review by Codegen\n\n"
            
            # Add general comments
            general_comments = [c for c in pr_review.comments if not c.file or not c.line]
            if general_comments:
                review_body += "## General Comments\n\n"
                for comment in general_comments:
                    review_body += f"- {comment.body}\n"
            
            # Determine the review state
            review_state = "COMMENT"
            if pr_review.status == PRReviewStatus.COMPLETED:
                review_state = "APPROVE"
            elif pr_review.status == PRReviewStatus.FAILED:
                review_state = "REQUEST_CHANGES"
            
            # Create the review
            result = pr.create_review(
                body=review_body,
                event=review_state,
                comments=review_comments
            )
            
            logger.info(f"Posted review to GitHub for PR #{pr_review.pr_number} in {pr_review.repo}")
            
            return {
                "success": True,
                "review_id": result.id,
                "review_state": review_state
            }
        
        except Exception as e:
            logger.error(f"Error posting review to GitHub: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }
    
    def auto_merge_pr(self, pr_review: PRReview) -> Dict[str, Any]:
        """Auto-merge a PR if it passes review and auto-merge is enabled.
        
        Args:
            pr_review: The PR review object
            
        Returns:
            Dictionary with the result of the merge operation
        """
        if not config.workflow.auto_merge_prs:
            logger.info(f"Auto-merge is disabled, skipping for PR #{pr_review.pr_number} in {pr_review.repo}")
            return {"success": False, "reason": "Auto-merge is disabled"}
        
        if pr_review.status != PRReviewStatus.COMPLETED:
            logger.info(f"PR review did not pass, skipping auto-merge for PR #{pr_review.pr_number} in {pr_review.repo}")
            return {"success": False, "reason": "PR review did not pass"}
        
        try:
            from github import Github
            
            # Create a GitHub client
            github_client = Github(self.github_token)
            
            # Get the repository and PR
            repo = github_client.get_repo(pr_review.repo)
            pr = repo.get_pull(pr_review.pr_number)
            
            # Check if the PR can be merged
            if not pr.mergeable:
                logger.info(f"PR #{pr_review.pr_number} in {pr_review.repo} is not mergeable")
                return {"success": False, "reason": "PR is not mergeable"}
            
            # Merge the PR
            merge_result = pr.merge(
                commit_title=f"Auto-merge PR #{pr_review.pr_number}: {pr.title}",
                commit_message=f"Auto-merged by Codegen after successful review",
                merge_method="merge"
            )
            
            logger.info(f"Auto-merged PR #{pr_review.pr_number} in {pr_review.repo}")
            
            return {
                "success": True,
                "merged": merge_result.merged,
                "message": merge_result.message
            }
        
        except Exception as e:
            logger.error(f"Error auto-merging PR: {e}")
            
            return {
                "success": False,
                "error": str(e)
            }

# Create a singleton instance
pr_review_agent = PRReviewAgentIntegration()