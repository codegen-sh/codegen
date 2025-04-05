"""
PR Review Agent Integration for Project Plan Manager.
This module integrates the PR Review Agent with the Project Plan Manager.
"""

import os
import logging
from typing import Dict, List, Any, Optional

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

# Create a singleton instance
pr_review_agent = PRReviewAgentIntegration()