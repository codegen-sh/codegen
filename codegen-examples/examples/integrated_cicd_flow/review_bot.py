"""Review Bot component for the integrated CI/CD flow.

This component reviews PRs and provides feedback via GitHub and Slack.
"""

import logging
import os
from typing import Dict, Any, List

import modal
from codegen import Codebase, CodeAgent
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.tools.semantic_search import semantic_search
from codegen.shared.enums.programming_language import ProgrammingLanguage
from fastapi import Request
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent

from shared.models import CodeReviewFeedback
from shared.utils import (
    create_codebase,
    notify_slack,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Modal image
image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install(
    "fastapi[standard]",
    "codegen>=0.22.2",
    "slack_sdk",
)

# Create CodegenApp
app = CodegenApp(name="review-bot")

# Default repository to analyze
DEFAULT_REPO = "codegen-sh/codegen-sdk"


@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class ReviewBot:
    """Review Bot for analyzing PRs and providing feedback."""

    codebase: Codebase

    @modal.enter()
    def initialize(self):
        """Initialize the Review Bot."""
        # Initialize codebase
        self.codebase = create_codebase(DEFAULT_REPO, ProgrammingLanguage.PYTHON)
        
        logger.info("Review Bot initialized")

    @app.github.event("pull_request:labeled")
    def handle_pr_labeled(self, event: PullRequestLabeledEvent):
        """Handle GitHub PR labeled events.
        
        Args:
            event: The webhook payload from GitHub
        """
        logger.info(f"Received PR labeled event: {event.label.name}")
        
        # Only process PRs with the "Codegen" label
        if event.label.name != "Codegen":
            logger.info(f"Ignoring PR with label: {event.label.name}")
            return
        
        logger.info(f"Processing PR #{event.number}: {event.pull_request.title}")
        
        # Notify Slack
        app.slack.client.chat_postMessage(
            channel="development",
            text=f"Starting review of PR #{event.number}: {event.pull_request.title}",
        )
        
        # Review the PR
        feedback = self._review_pr(event)
        
        # Post feedback to GitHub
        self._post_feedback_to_github(event, feedback)
        
        # Post feedback to Slack
        self._post_feedback_to_slack(event, feedback)
        
        logger.info(f"Completed review of PR #{event.number}")
    
    def _review_pr(self, event: PullRequestLabeledEvent) -> CodeReviewFeedback:
        """Review a PR and generate feedback.
        
        Args:
            event: The PR event
            
        Returns:
            Feedback from the review
        """
        # Get the PR details
        pr_number = event.number
        pr_title = event.pull_request.title
        pr_url = event.pull_request.html_url
        
        # Use CodeAgent to analyze the PR
        agent = CodeAgent(self.codebase)
        
        # This is a simplified implementation
        # In a real implementation, you would use the agent to analyze the PR
        # and generate feedback
        
        # Create feedback
        feedback = CodeReviewFeedback(
            pr_url=pr_url,
            overall_assessment="The code looks good overall, with some minor issues to address.",
            suggestions=[
                "Consider adding more unit tests",
                "Add docstrings to new functions",
            ],
            security_issues=[],
            performance_issues=[],
            style_issues=[
                "Use consistent naming conventions",
            ],
            positive_aspects=[
                "Good separation of concerns",
                "Clear implementation of the feature",
            ],
        )
        
        return feedback
    
    def _post_feedback_to_github(self, event: PullRequestLabeledEvent, feedback: CodeReviewFeedback):
        """Post feedback to GitHub.
        
        Args:
            event: The PR event
            feedback: The feedback to post
        """
        # Format the feedback
        comment = self._format_feedback_for_github(feedback)
        
        # Post the comment
        app.github.client.issues.create_comment(
            owner=event.repository.owner.login,
            repo=event.repository.name,
            issue_number=event.number,
            body=comment,
        )
    
    def _post_feedback_to_slack(self, event: PullRequestLabeledEvent, feedback: CodeReviewFeedback):
        """Post feedback to Slack.
        
        Args:
            event: The PR event
            feedback: The feedback to post
        """
        # Format the feedback
        message = self._format_feedback_for_slack(event, feedback)
        
        # Post the message
        app.slack.client.chat_postMessage(
            channel="development",
            text=message,
        )
    
    def _format_feedback_for_github(self, feedback: CodeReviewFeedback) -> str:
        """Format feedback for GitHub.
        
        Args:
            feedback: The feedback to format
            
        Returns:
            Formatted feedback
        """
        result = "## Code Review Feedback\n\n"
        result += f"### Overall Assessment\n{feedback.overall_assessment}\n\n"
        
        if feedback.positive_aspects:
            result += "### Positive Aspects\n"
            for aspect in feedback.positive_aspects:
                result += f"- ✅ {aspect}\n"
            result += "\n"
        
        if feedback.suggestions:
            result += "### Suggestions\n"
            for suggestion in feedback.suggestions:
                result += f"- 💡 {suggestion}\n"
            result += "\n"
        
        if feedback.security_issues:
            result += "### Security Issues\n"
            for issue in feedback.security_issues:
                result += f"- 🔒 {issue}\n"
            result += "\n"
        
        if feedback.performance_issues:
            result += "### Performance Issues\n"
            for issue in feedback.performance_issues:
                result += f"- ⚡ {issue}\n"
            result += "\n"
        
        if feedback.style_issues:
            result += "### Style Issues\n"
            for issue in feedback.style_issues:
                result += f"- 🎨 {issue}\n"
            result += "\n"
        
        return result
    
    def _format_feedback_for_slack(self, event: PullRequestLabeledEvent, feedback: CodeReviewFeedback) -> str:
        """Format feedback for Slack.
        
        Args:
            event: The PR event
            feedback: The feedback to format
            
        Returns:
            Formatted feedback
        """
        result = f"*Code Review for <{feedback.pr_url}|PR #{event.number}: {event.pull_request.title}>*\n\n"
        result += f"*Overall Assessment*: {feedback.overall_assessment}\n\n"
        
        if feedback.positive_aspects:
            result += "*Positive Aspects*:\n"
            for aspect in feedback.positive_aspects:
                result += f"• ✅ {aspect}\n"
            result += "\n"
        
        if feedback.suggestions:
            result += "*Suggestions*:\n"
            for suggestion in feedback.suggestions:
                result += f"• 💡 {suggestion}\n"
            result += "\n"
        
        if feedback.security_issues or feedback.performance_issues or feedback.style_issues:
            result += "*Issues*:\n"
            for issue in feedback.security_issues:
                result += f"• 🔒 {issue}\n"
            for issue in feedback.performance_issues:
                result += f"• ⚡ {issue}\n"
            for issue in feedback.style_issues:
                result += f"• 🎨 {issue}\n"
        
        return result


@app.function(secrets=[modal.Secret.from_dotenv()])
@modal.web_endpoint(method="POST")
def github_webhook(event: Dict[str, Any], request: Request):
    """Handle GitHub webhook events.
    
    Args:
        event: The webhook payload from GitHub
        request: The FastAPI request object
        
    Returns:
        A response indicating success or failure
    """
    logger.info("Received GitHub webhook event")
    return app.github.handle(event, request)


if __name__ == "__main__":
    # For local development
    modal.runner.deploy_stub("review-bot")