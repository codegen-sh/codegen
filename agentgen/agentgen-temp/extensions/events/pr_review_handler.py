"""
PR Review Handler for GitHub events.
"""

import logging
import os
from typing import Dict, Any, Optional

from github import Github
from pydantic import BaseModel

from codegen.agents.pr_review_agent import PRReviewAgent
from codegen.extensions.github.types.events.pull_request import PullRequestEvent
from codegen.extensions.planning.manager import PlanManager
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class PRReviewHandler:
    """Handler for PR review events."""
    
    def __init__(
        self,
        github_token: Optional[str] = None,
        slack_token: Optional[str] = None,
        slack_channel_id: Optional[str] = None,
        output_dir: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ):
        """Initialize the PR review handler."""
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        self.slack_token = slack_token or os.environ.get("SLACK_BOT_TOKEN", "")
        self.slack_channel_id = slack_channel_id or os.environ.get("SLACK_CHANNEL_ID", "")
        self.output_dir = output_dir or os.environ.get("OUTPUT_DIR", "output")
        self.anthropic_api_key = anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY", "")
        
        # Initialize GitHub client
        if not self.github_token:
            raise ValueError("GitHub token is required")
        
        self.github_client = Github(self.github_token)
        
        # Initialize plan manager
        self.plan_manager = PlanManager(
            output_dir=self.output_dir,
            anthropic_api_key=self.anthropic_api_key,
            openai_api_key=self.openai_api_key,
        )
    
    def handle_pr_event(self, event: PullRequestEvent) -> Dict[str, Any]:
        """Handle a pull request event."""
        logger.info(f"Handling PR event: {event.action} for PR #{event.number} in {event.repository.full_name}")
        
        # Only process opened, reopened, or synchronized PRs
        if event.action not in ["opened", "reopened", "synchronize"]:
            logger.info(f"Ignoring PR event with action: {event.action}")
            return {"status": "ignored", "reason": f"Action {event.action} not processed"}
        
        try:
            # Get repository and PR details
            repo_name = event.repository.full_name
            pr_number = event.number
            
            # Create a codebase instance for the repository
            from codegen import Codebase
            codebase = Codebase(repo_name, github_token=self.github_token)
            
            # Create a PR review agent
            pr_review_agent = PRReviewAgent(
                codebase=codebase,
                github_token=self.github_token,
                slack_token=self.slack_token,
                slack_channel_id=self.slack_channel_id,
                output_dir=self.output_dir,
                model_provider="anthropic" if self.anthropic_api_key else "openai",
                model_name="claude-3-7-sonnet-latest" if self.anthropic_api_key else "gpt-4-turbo",
            )
            
            # Review the PR
            review_result = pr_review_agent.review_pr(repo_name, pr_number)
            
            return {
                "status": "success",
                "pr_number": pr_number,
                "repo_name": repo_name,
                "review_result": review_result,
            }
        
        except Exception as e:
            logger.error(f"Error handling PR event: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "error": str(e),
                "pr_number": event.number,
                "repo_name": event.repository.full_name,
            }
    
    def handle_slack_command(self, command: str, text: str, user_id: str, channel_id: str) -> Dict[str, Any]:
        """Handle a Slack command."""
        logger.info(f"Handling Slack command: {command} with text: {text}")
        
        try:
            if command == "/review-pr":
                # Parse the PR URL or repo/number format
                import re
                
                # Try to match GitHub URL format
                url_match = re.search(r'github\.com/([^/]+/[^/]+)/pull/(\d+)', text)
                if url_match:
                    repo_name = url_match.group(1)
                    pr_number = int(url_match.group(2))
                else:
                    # Try to match repo#number format
                    repo_pr_match = re.search(r'([^#]+)#(\d+)', text)
                    if repo_pr_match:
                        repo_name = repo_pr_match.group(1)
                        pr_number = int(repo_pr_match.group(2))
                    else:
                        return {
                            "status": "error",
                            "error": "Invalid PR format. Use a GitHub URL or repo#number format.",
                            "response_text": "Invalid PR format. Please use a GitHub URL (https://github.com/owner/repo/pull/123) or repo#number format (owner/repo#123).",
                        }
                
                # Create a codebase instance for the repository
                from codegen import Codebase
                codebase = Codebase(repo_name, github_token=self.github_token)
                
                # Create a PR review agent
                pr_review_agent = PRReviewAgent(
                    codebase=codebase,
                    github_token=self.github_token,
                    slack_token=self.slack_token,
                    slack_channel_id=channel_id,
                    output_dir=self.output_dir,
                    model_provider="anthropic" if self.anthropic_api_key else "openai",
                    model_name="claude-3-7-sonnet-latest" if self.anthropic_api_key else "gpt-4-turbo",
                )
                
                # Send initial response
                from slack_sdk import WebClient
                slack_client = WebClient(token=self.slack_token)
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=f"Starting review of PR #{pr_number} in {repo_name}... This may take a few minutes."
                )
                
                # Review the PR
                review_result = pr_review_agent.review_pr(repo_name, pr_number)
                
                return {
                    "status": "success",
                    "pr_number": pr_number,
                    "repo_name": repo_name,
                    "review_result": review_result,
                }
            
            elif command == "/create-plan":
                # Format should be: title | description | markdown_url
                parts = text.split("|")
                if len(parts) != 3:
                    return {
                        "status": "error",
                        "error": "Invalid format. Use: title | description | markdown_url",
                        "response_text": "Invalid format. Please use: title | description | markdown_url",
                    }
                
                title = parts[0].strip()
                description = parts[1].strip()
                markdown_url = parts[2].strip()
                
                # Fetch the markdown content
                import requests
                response = requests.get(markdown_url)
                if response.status_code != 200:
                    return {
                        "status": "error",
                        "error": f"Failed to fetch markdown content: {response.status_code}",
                        "response_text": f"Failed to fetch markdown content: {response.status_code}",
                    }
                
                markdown_content = response.text
                
                # Create a plan
                plan = self.plan_manager.create_plan_from_markdown(markdown_content, title, description)
                
                # Generate a progress report
                progress_report = self.plan_manager.generate_progress_report()
                
                # Send response
                from slack_sdk import WebClient
                slack_client = WebClient(token=self.slack_token)
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=f"Created plan: {title}\n\n{progress_report[:1000]}...\n\nSee the full report in the output directory."
                )
                
                return {
                    "status": "success",
                    "plan_title": title,
                    "plan_description": description,
                }
            
            elif command == "/next-step":
                # Get the next step
                next_step = self.plan_manager.get_next_step()
                if not next_step:
                    return {
                        "status": "error",
                        "error": "No pending steps found",
                        "response_text": "No pending steps found in the current plan.",
                    }
                
                # Update step status to in_progress
                self.plan_manager.update_step_status(next_step.id, "in_progress")
                
                # Send response
                from slack_sdk import WebClient
                slack_client = WebClient(token=self.slack_token)
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=f"Next step: {next_step.description}\n\nPlease implement this step and create a PR with the step ID ({next_step.id}) in the title or description."
                )
                
                return {
                    "status": "success",
                    "step_id": next_step.id,
                    "step_description": next_step.description,
                }
            
            elif command == "/progress-report":
                # Generate a progress report
                progress_report = self.plan_manager.generate_progress_report()
                
                # Send response
                from slack_sdk import WebClient
                slack_client = WebClient(token=self.slack_token)
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=f"Progress Report:\n\n{progress_report[:1000]}...\n\nSee the full report in the output directory."
                )
                
                return {
                    "status": "success",
                    "progress_report": progress_report[:1000],
                }
            
            else:
                return {
                    "status": "error",
                    "error": f"Unknown command: {command}",
                    "response_text": f"Unknown command: {command}",
                }
        
        except Exception as e:
            logger.error(f"Error handling Slack command: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "error": str(e),
                "command": command,
                "text": text,
            }


def register_pr_review_handlers(app):
    """Register PR review handlers with the app."""
    
    # Initialize the PR review handler
    pr_review_handler = PRReviewHandler(
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        slack_token=os.environ.get("SLACK_BOT_TOKEN", ""),
        slack_channel_id=os.environ.get("SLACK_CHANNEL_ID", ""),
        output_dir=os.environ.get("OUTPUT_DIR", "output"),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
    )
    
    # Register GitHub event handlers
    @app.github.event("pull_request:opened")
    def handle_pr_opened(event: PullRequestEvent):
        return pr_review_handler.handle_pr_event(event)
    
    @app.github.event("pull_request:reopened")
    def handle_pr_reopened(event: PullRequestEvent):
        return pr_review_handler.handle_pr_event(event)
    
    @app.github.event("pull_request:synchronize")
    def handle_pr_synchronize(event: PullRequestEvent):
        return pr_review_handler.handle_pr_event(event)
    
    # Register Slack command handlers
    @app.slack.event("app_mention")
    async def handle_app_mention(event):
        # Parse the message text
        text = event.text
        user_id = event.user
        channel_id = event.channel
        
        # Check if this is a command
        if "review pr" in text.lower():
            # Extract the PR URL or reference
            import re
            pr_ref_match = re.search(r'review pr\s+(.+)', text.lower())
            if pr_ref_match:
                pr_ref = pr_ref_match.group(1).strip()
                return pr_review_handler.handle_slack_command("/review-pr", pr_ref, user_id, channel_id)
        
        elif "create plan" in text.lower():
            # Extract the plan details
            import re
            plan_match = re.search(r'create plan\s+(.+)', text.lower())
            if plan_match:
                plan_details = plan_match.group(1).strip()
                return pr_review_handler.handle_slack_command("/create-plan", plan_details, user_id, channel_id)
        
        elif "next step" in text.lower():
            return pr_review_handler.handle_slack_command("/next-step", "", user_id, channel_id)
        
        elif "progress report" in text.lower():
            return pr_review_handler.handle_slack_command("/progress-report", "", user_id, channel_id)
        
        # Default response
        from slack_sdk import WebClient
        slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN", ""))
        slack_client.chat_postMessage(
            channel=channel_id,
            text=f"Hello <@{user_id}>! I'm the PR Code Review agent. You can ask me to:\n"
                 f"- review PR [URL or repo#number]\n"
                 f"- create plan [title | description | markdown_url]\n"
                 f"- next step\n"
                 f"- progress report"
        )
        
        return {"status": "success", "message": "Responded to app mention"}
