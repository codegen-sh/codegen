"""
PR Review Handler for GitHub events.
"""

import os
import json
import logging
import traceback
from typing import Dict, List, Any, Optional, Callable, Union

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest

from agentgen.extensions.github.types.events import PullRequestEvent
from agentgen.agents.pr_review.agent import PRReviewAgent
from agentgen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRReviewHandler:
    """Handler for PR review events."""
    
    def __init__(
        self,
        github_token: Optional[str] = None,
        slack_token: Optional[str] = None,
        slack_channel_id: Optional[str] = None,
        output_dir: Optional[str] = None,
    ):
        """Initialize the PR review handler."""
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        self.github_client = Github(self.github_token)
        
        self.slack_token = slack_token or os.environ.get("SLACK_BOT_TOKEN", "")
        self.slack_channel_id = slack_channel_id or os.environ.get("SLACK_CHANNEL_ID", "")
        
        self.output_dir = output_dir or os.environ.get("OUTPUT_DIR", "output")
        
        # Initialize Slack client if tokens are provided
        if self.slack_token:
            self.slack_client = WebClient(token=self.slack_token)
        else:
            self.slack_client = None
    
    def handle_pr_opened(self, event: PullRequestEvent) -> Dict[str, Any]:
        """Handle a PR opened event."""
        logger.info(f"Handling PR opened event: {event.repository.full_name}#{event.pull_request.number}")
        
        repo_name = event.repository.full_name
        pr_number = event.pull_request.number
        
        # Create a PR review agent
        agent = PRReviewAgent(
            codebase=repo_name,
            github_token=self.github_token,
            slack_token=self.slack_token,
            slack_channel_id=self.slack_channel_id,
            output_dir=self.output_dir,
        )
        
        # Review the PR
        review_result = agent.review_pr(repo_name, pr_number)
        
        # Send notification to Slack if configured
        if self.slack_client and self.slack_channel_id:
            self._send_slack_notification(repo_name, pr_number, review_result)
        
        return review_result
    
    def handle_pr_synchronize(self, event: PullRequestEvent) -> Dict[str, Any]:
        """Handle a PR synchronize event (new commits pushed)."""
        logger.info(f"Handling PR synchronize event: {event.repository.full_name}#{event.pull_request.number}")
        
        repo_name = event.repository.full_name
        pr_number = event.pull_request.number
        
        # Create a PR review agent
        agent = PRReviewAgent(
            codebase=repo_name,
            github_token=self.github_token,
            slack_token=self.slack_token,
            slack_channel_id=self.slack_channel_id,
            output_dir=self.output_dir,
        )
        
        # Review the PR
        review_result = agent.review_pr(repo_name, pr_number)
        
        # Send notification to Slack if configured
        if self.slack_client and self.slack_channel_id:
            self._send_slack_notification(repo_name, pr_number, review_result, is_update=True)
        
        return review_result
    
    def handle_pr_labeled(self, event: PullRequestEvent) -> Optional[Dict[str, Any]]:
        """Handle a PR labeled event."""
        logger.info(f"Handling PR labeled event: {event.repository.full_name}#{event.pull_request.number}")
        
        # Check if the label is "needs-review"
        if event.label.name.lower() != "needs-review":
            logger.info(f"Ignoring PR labeled event with label: {event.label.name}")
            return None
        
        repo_name = event.repository.full_name
        pr_number = event.pull_request.number
        
        # Create a PR review agent
        agent = PRReviewAgent(
            codebase=repo_name,
            github_token=self.github_token,
            slack_token=self.slack_token,
            slack_channel_id=self.slack_channel_id,
            output_dir=self.output_dir,
        )
        
        # Review the PR
        review_result = agent.review_pr(repo_name, pr_number)
        
        # Send notification to Slack if configured
        if self.slack_client and self.slack_channel_id:
            self._send_slack_notification(repo_name, pr_number, review_result)
        
        return review_result
    
    def handle_slack_command(self, command_text: str, channel_id: str, user_id: str) -> Dict[str, Any]:
        """Handle a Slack command to review a PR."""
        logger.info(f"Handling Slack command: {command_text}")
        
        # Parse the command text to extract repo and PR number
        # Expected format: "review repo_owner/repo_name#pr_number"
        parts = command_text.strip().split()
        
        if len(parts) < 2 or parts[0].lower() != "review":
            return {
                "text": "Invalid command format. Use: review owner/repo#pr_number",
                "response_type": "ephemeral",
            }
        
        # Parse repo and PR number
        repo_pr = parts[1]
        if "#" not in repo_pr:
            return {
                "text": "Invalid format. Use: review owner/repo#pr_number",
                "response_type": "ephemeral",
            }
        
        repo_name, pr_number_str = repo_pr.split("#", 1)
        
        try:
            pr_number = int(pr_number_str)
        except ValueError:
            return {
                "text": f"Invalid PR number: {pr_number_str}",
                "response_type": "ephemeral",
            }
        
        # Create a PR review agent
        agent = PRReviewAgent(
            codebase=repo_name,
            github_token=self.github_token,
            slack_token=self.slack_token,
            slack_channel_id=channel_id,  # Use the channel where the command was issued
            output_dir=self.output_dir,
        )
        
        # Send initial response
        initial_response = {
            "text": f"Reviewing PR #{pr_number} in {repo_name}...",
            "response_type": "in_channel",
        }
        
        # Review the PR
        try:
            review_result = agent.review_pr(repo_name, pr_number)
            
            # The agent will send the notification to Slack directly
            return initial_response
            
        except Exception as e:
            logger.error(f"Error reviewing PR: {e}")
            
            return {
                "text": f"Error reviewing PR: {e}",
                "response_type": "in_channel",
            }
    
    def _send_slack_notification(self, repo_name: str, pr_number: int, review_result: Dict[str, Any], is_update: bool = False) -> None:
        """Send a notification to Slack about the PR review."""
        if not self.slack_client or not self.slack_channel_id:
            return
        
        try:
            message = f"*{'Updated ' if is_update else ''}PR Review Result for {repo_name}#{pr_number}*\n\n"
            
            if review_result.get("compliant", False):
                message += ":white_check_mark: *This PR complies with project requirements.*\n\n"
                
                if review_result.get("approval_recommendation") == "approve":
                    message += ":rocket: *The PR has been automatically approved and merged.*\n\n"
            else:
                message += ":x: *This PR does not fully comply with project requirements.*\n\n"
            
            issues = review_result.get("issues", [])
            if issues and len(issues) > 0:
                message += "*Issues:*\n"
                for issue in issues:
                    message += f"- {issue}\n"
                message += "\n"
            
            suggestions = review_result.get("suggestions", [])
            if suggestions and len(suggestions) > 0:
                message += "*Suggestions:*\n"
                for suggestion in suggestions:
                    if isinstance(suggestion, dict):
                        desc = suggestion.get("description", "")
                        file_path = suggestion.get("file_path")
                        line_number = suggestion.get("line_number")
                        
                        if file_path and line_number:
                            message += f"- {desc} (in `{file_path}` at line {line_number})\n"
                        elif file_path:
                            message += f"- {desc} (in `{file_path}`)\n"
                        else:
                            message += f"- {desc}\n"
                    else:
                        message += f"- {suggestion}\n"
                message += "\n"
            
            if review_result.get("approval_recommendation") == "approve":
                message += ":thumbsup: *Recommendation: Approve*\n"
            else:
                message += ":thumbsdown: *Recommendation: Request Changes*\n"
            
            message += f"\n<https://github.com/{repo_name}/pull/{pr_number}|View PR on GitHub>"
            
            self.slack_client.chat_postMessage(
                channel=self.slack_channel_id,
                text=message
            )
            
            logger.info(f"Sent PR review notification to Slack channel {self.slack_channel_id}")
        
        except Exception as e:
            logger.error(f"Error sending Slack notification: {e}")


def register_pr_review_handlers(app):
    """Register PR review handlers with the app."""
    
    # Initialize the PR review handler
    handler = PRReviewHandler(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        slack_token=os.environ.get("SLACK_BOT_TOKEN", ""),
        slack_channel_id=os.environ.get("SLACK_CHANNEL_ID", ""),
        output_dir=os.environ.get("OUTPUT_DIR", "output"),
    )
    
    # Register GitHub webhook handlers
    @app.route("/webhooks/github", methods=["POST"])
    def github_webhook():
        """Handle GitHub webhook events."""
        payload = app.request.json
        event_type = app.request.headers.get("X-GitHub-Event")
        
        if event_type == "pull_request":
            action = payload.get("action")
            
            if action == "opened":
                event = PullRequestEvent.from_dict(payload)
                handler.handle_pr_opened(event)
                return {"status": "success", "message": "PR opened event handled"}
            
            elif action == "synchronize":
                event = PullRequestEvent.from_dict(payload)
                handler.handle_pr_synchronize(event)
                return {"status": "success", "message": "PR synchronize event handled"}
            
            elif action == "labeled":
                event = PullRequestEvent.from_dict(payload)
                handler.handle_pr_labeled(event)
                return {"status": "success", "message": "PR labeled event handled"}
        
        return {"status": "ignored", "message": f"Ignored event: {event_type}/{payload.get('action')}"}
    
    # Register Slack command handler
    @app.route("/slack/commands/review", methods=["POST"])
    def slack_review_command():
        """Handle Slack /review command."""
        form_data = app.request.form
        
        command_text = form_data.get("text", "")
        channel_id = form_data.get("channel_id", "")
        user_id = form_data.get("user_id", "")
        
        response = handler.handle_slack_command(command_text, channel_id, user_id)
        
        return response
