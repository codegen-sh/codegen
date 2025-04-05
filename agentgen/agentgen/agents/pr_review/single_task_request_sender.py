"""
Single task request sender for PR Code Review agent.
"""

import os
import re
import json
import logging
import time
import traceback
from typing import Dict, List, Optional, Any, Tuple, Union
from uuid import uuid4

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from codegen.extensions.planning.manager import PlanManager, Step
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


class SingleTaskRequestSender:
    """Sends task requests to Slack and waits for responses."""
    
    def __init__(
        self,
        slack_token: Optional[str] = None,
        slack_channel_id: Optional[str] = None,
        output_dir: Optional[str] = None,
        wait_for_response: bool = True,
        response_timeout: int = 3600,  # 1 hour
        github_token: Optional[str] = None,
    ):
        """Initialize the task request sender.
        
        Args:
            slack_token: Slack token for API access
            slack_channel_id: Slack channel ID for notifications
            output_dir: Directory for output files
            wait_for_response: Whether to wait for a response
            response_timeout: Timeout in seconds for waiting for a response
            github_token: GitHub token for API access
        """
        self.slack_token = slack_token or os.environ.get("SLACK_BOT_TOKEN", "")
        if not self.slack_token:
            raise ValueError("Slack token is required")
        
        self.slack_channel_id = slack_channel_id or os.environ.get("SLACK_CHANNEL_ID", "")
        if not self.slack_channel_id:
            raise ValueError("Slack channel ID is required")
        
        self.output_dir = output_dir or os.environ.get("OUTPUT_DIR", "output")
        
        self.wait_for_response = wait_for_response
        self.response_timeout = response_timeout
        
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")
        
        # Initialize Slack client
        self.slack_client = WebClient(token=self.slack_token)
        
        # Initialize plan manager
        self.plan_manager = PlanManager(
            output_dir=self.output_dir,
            anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
            openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
        )
    
    def send_task_request(self, task_description: str, step_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a task request to Slack.
        
        Args:
            task_description: Description of the task
            step_id: ID of the step in the plan
            context: Additional context for the task
            
        Returns:
            Dictionary with the result
        """
        logger.info(f"Sending task request: {task_description}")
        
        # Update step status if provided
        if step_id:
            self.plan_manager.update_step_status(
                step_id=step_id,
                status="in_progress",
                details=f"Task request sent: {task_description}"
            )
        
        # Format the message
        message = self._format_task_message(task_description, step_id, context)
        
        try:
            # Send the message
            response = self.slack_client.chat_postMessage(
                channel=self.slack_channel_id,
                text=message,
                unfurl_links=False,
                unfurl_media=False,
            )
            
            # Get the timestamp of the message
            ts = response["ts"]
            
            logger.info(f"Task request sent with timestamp: {ts}")
            
            # Wait for a response if configured
            if self.wait_for_response:
                response_result = self._wait_for_response(ts)
                
                # Update step status if provided
                if step_id and response_result.get("completed", False):
                    self.plan_manager.update_step_status(
                        step_id=step_id,
                        status="completed",
                        details=f"Task completed: {task_description}"
                    )
                
                return {
                    "status": "success",
                    "task_description": task_description,
                    "step_id": step_id,
                    "message_ts": ts,
                    "response": response_result,
                }
            
            return {
                "status": "success",
                "task_description": task_description,
                "step_id": step_id,
                "message_ts": ts,
            }
        
        except SlackApiError as e:
            logger.error(f"Error sending task request: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "error": str(e),
                "task_description": task_description,
                "step_id": step_id,
            }
    
    def send_next_step_request(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Send a request for the next step in the plan.
        
        Args:
            context: Additional context for the task
            
        Returns:
            Dictionary with the result
        """
        # Get the next step
        next_step = self.plan_manager.get_next_step()
        if not next_step:
            logger.info("No pending steps found")
            
            return {
                "status": "error",
                "error": "No pending steps found",
            }
        
        # Send the task request
        return self.send_task_request(next_step.description, next_step.id, context)
    
    def send_pr_review_request(self, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Send a request to review a PR.
        
        Args:
            repo_name: Name of the repository
            pr_number: Number of the PR
            
        Returns:
            Dictionary with the result
        """
        logger.info(f"Sending PR review request for {repo_name}#{pr_number}")
        
        # Format the message
        message = self._format_pr_review_message(repo_name, pr_number)
        
        try:
            # Send the message
            response = self.slack_client.chat_postMessage(
                channel=self.slack_channel_id,
                text=message,
                unfurl_links=False,
                unfurl_media=False,
            )
            
            # Get the timestamp of the message
            ts = response["ts"]
            
            logger.info(f"PR review request sent with timestamp: {ts}")
            
            # Wait for a response if configured
            if self.wait_for_response:
                response_result = self._wait_for_response(ts)
                
                return {
                    "status": "success",
                    "repo_name": repo_name,
                    "pr_number": pr_number,
                    "message_ts": ts,
                    "response": response_result,
                }
            
            return {
                "status": "success",
                "repo_name": repo_name,
                "pr_number": pr_number,
                "message_ts": ts,
            }
        
        except SlackApiError as e:
            logger.error(f"Error sending PR review request: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "error": str(e),
                "repo_name": repo_name,
                "pr_number": pr_number,
            }
    
    def send_progress_report(self) -> Dict[str, Any]:
        """Send a progress report to Slack.
        
        Returns:
            Dictionary with the result
        """
        logger.info("Generating progress report")
        
        # Generate the progress report
        progress_report = self.plan_manager.generate_progress_report()
        
        # Format the message
        message = f"*Project Progress Report*\n\n{progress_report}"
        
        try:
            # Send the message
            response = self.slack_client.chat_postMessage(
                channel=self.slack_channel_id,
                text=message,
                unfurl_links=True,
                unfurl_media=True,
            )
            
            # Get the timestamp of the message
            ts = response["ts"]
            
            logger.info(f"Progress report sent with timestamp: {ts}")
            
            return {
                "status": "success",
                "message_ts": ts,
            }
        
        except SlackApiError as e:
            logger.error(f"Error sending progress report: {e}")
            logger.error(traceback.format_exc())
            
            return {
                "status": "error",
                "error": str(e),
            }
    
    def _format_task_message(self, task_description: str, step_id: Optional[str] = None, context: Optional[Dict[str, Any]] = None) -> str:
        """Format a task message for Slack.
        
        Args:
            task_description: Description of the task
            step_id: ID of the step in the plan
            context: Additional context for the task
            
        Returns:
            Formatted message
        """
        message = f"*Task Request*\n\n"
        
        if step_id:
            message += f"*Step ID:* {step_id}\n\n"
        
        message += f"*Task:* {task_description}\n\n"
        
        if context:
            message += "*Context:*\n"
            for key, value in context.items():
                message += f"- *{key}:* {value}\n"
            message += "\n"
        
        # Add instructions
        message += "Please implement this task and create a PR. "
        message += "Once completed, reply to this message with the PR link."
        
        return message
    
    def _format_pr_review_message(self, repo_name: str, pr_number: int) -> str:
        """Format a PR review message for Slack.
        
        Args:
            repo_name: Name of the repository
            pr_number: Number of the PR
            
        Returns:
            Formatted message
        """
        message = f"*PR Review Request*\n\n"
        
        message += f"*Repository:* {repo_name}\n"
        message += f"*PR Number:* {pr_number}\n\n"
        
        message += f"Please review <https://github.com/{repo_name}/pull/{pr_number}|PR #{pr_number}> "
        message += "and provide feedback. Once completed, reply to this message with your review."
        
        return message
    
    def _wait_for_response(self, message_ts: str) -> Dict[str, Any]:
        """Wait for a response to a task request.
        
        Args:
            message_ts: Timestamp of the message to wait for a response to
            
        Returns:
            Dictionary with the response
        """
        logger.info(f"Waiting for response to message {message_ts}")
        
        start_time = time.time()
        
        while time.time() - start_time < self.response_timeout:
            try:
                # Get the replies to the message
                response = self.slack_client.conversations_replies(
                    channel=self.slack_channel_id,
                    ts=message_ts,
                )
                
                # Check if there are any replies
                messages = response.get("messages", [])
                if len(messages) > 1:
                    # Get the latest reply
                    latest_reply = messages[-1]
                    
                    # Check if the reply contains a PR link
                    pr_link_match = re.search(r'https://github\.com/[^/]+/[^/]+/pull/\d+', latest_reply.get("text", ""))
                    if pr_link_match:
                        pr_link = pr_link_match.group(0)
                        
                        logger.info(f"Found PR link in response: {pr_link}")
                        
                        return {
                            "completed": True,
                            "pr_link": pr_link,
                            "response_text": latest_reply.get("text", ""),
                            "response_ts": latest_reply.get("ts", ""),
                        }
                    
                    # If no PR link, but there's a reply, consider it a response
                    if latest_reply.get("text", "").strip():
                        logger.info(f"Found response: {latest_reply.get('text', '')}")
                        
                        return {
                            "completed": True,
                            "response_text": latest_reply.get("text", ""),
                            "response_ts": latest_reply.get("ts", ""),
                        }
                
                # Sleep for a bit before checking again
                time.sleep(60)  # Check every minute
            
            except SlackApiError as e:
                logger.error(f"Error checking for response: {e}")
                logger.error(traceback.format_exc())
                
                # Sleep for a bit before trying again
                time.sleep(60)
        
        logger.info(f"Timed out waiting for response to message {message_ts}")
        
        return {
            "completed": False,
            "error": "Timed out waiting for response",
        }
