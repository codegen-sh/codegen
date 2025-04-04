"""
Slack service for communicating with Codegen.
"""

import logging
import os
from typing import Dict, List, Optional, Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from ..models import Requirement

logger = logging.getLogger("integrated_pr_agent")


class SlackService:
    """Service for communicating with Slack."""
    
    def __init__(self, slack_token: Optional[str] = None, channel_id: Optional[str] = None):
        """Initialize the Slack service."""
        self.slack_token = slack_token or os.environ.get("SLACK_BOT_TOKEN", "")
        self.channel_id = channel_id or os.environ.get("SLACK_CHANNEL_ID", "")
        self.codegen_user_id = os.environ.get("CODEGEN_USER_ID", "")
        
        if not self.slack_token:
            raise ValueError("Slack token is required")
        
        if not self.channel_id:
            raise ValueError("Slack channel ID is required")
        
        self.client = WebClient(token=self.slack_token)
    
    def send_message(self, message: str) -> Dict[str, Any]:
        """Send a message to the Slack channel."""
        try:
            response = self.client.chat_postMessage(
                channel=self.channel_id,
                text=message,
            )
            return response
        except SlackApiError as e:
            logger.error(f"Error sending message: {e}")
            return {"ok": False, "error": str(e)}
    
    def send_requirement_request(self, requirement: Requirement) -> Dict[str, Any]:
        """Send a requirement request to Codegen."""
        message = f"<@{self.codegen_user_id}> I need help implementing the following requirement:\n\n"
        message += f"*Requirement*: {requirement.description}\n"
        message += f"*Section*: {requirement.section}\n"
        message += f"*Source*: {requirement.source}\n\n"
        message += "Please provide a step-by-step implementation plan for this requirement."
        
        return self.send_message(message)
    
    def send_pr_review_result(self, pr_number: int, review_result: Dict[str, Any]) -> Dict[str, Any]:
        """Send a PR review result to the Slack channel."""
        message = f"*PR Review Result for PR #{pr_number}*\n\n"
        
        if review_result["compliant"]:
            message += ":white_check_mark: *This PR complies with project requirements.*\n\n"
        else:
            message += ":x: *This PR does not fully comply with project requirements.*\n\n"
        
        # Add issues if any
        if review_result.get("issues") and len(review_result["issues"]) > 0:
            message += "*Issues:*\n"
            for issue in review_result["issues"]:
                message += f"- {issue}\n"
            message += "\n"
        
        # Add suggestions if any
        if review_result.get("suggestions") and len(review_result["suggestions"]) > 0:
            message += "*Suggestions:*\n"
            for suggestion in review_result["suggestions"]:
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
        
        # Add approval recommendation
        if review_result.get("approval_recommendation") == "approve":
            message += ":thumbsup: *Recommendation: Approve*\n"
        else:
            message += ":thumbsdown: *Recommendation: Request Changes*\n"
        
        return self.send_message(message)
    
    def get_messages(self, timestamp: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get messages from the Slack channel."""
        try:
            response = self.client.conversations_history(
                channel=self.channel_id,
                oldest=timestamp,
            )
            return response["messages"]
        except SlackApiError as e:
            logger.error(f"Error getting messages: {e}")
            return []
    
    def parse_codegen_response(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse Codegen responses from messages."""
        responses = []
        for message in messages:
            if message.get("user") == self.codegen_user_id:
                responses.append(
                    {
                        "text": message.get("text", ""),
                        "timestamp": message.get("ts", ""),
                    }
                )
        return responses