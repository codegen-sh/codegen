"""
Slack integration module for the integrated agent application.
"""

import logging
import os
from typing import Dict, List, Optional, Union, Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from .models import Requirement, PRReview, SlackMessage

logger = logging.getLogger(__name__)

class SlackIntegration:
    """Slack integration for the integrated agent application."""

    def __init__(self, token: Optional[str] = None, channel: Optional[str] = None):
        """Initialize the Slack integration.
        
        Args:
            token: Slack bot token. If not provided, will use SLACK_BOT_TOKEN environment variable.
            channel: Default channel ID to send messages to. If not provided, will use SLACK_CHANNEL environment variable.
        """
        self.token = token or os.environ.get("SLACK_BOT_TOKEN")
        if not self.token:
            raise ValueError("Slack bot token not provided")
        
        self.channel = channel or os.environ.get("SLACK_CHANNEL")
        self.client = WebClient(token=self.token)
        self.codegen_user_id = os.environ.get("CODEGEN_USER_ID")
        
        # Verify the token is valid
        try:
            self.client.auth_test()
            logger.info("Slack authentication successful")
        except SlackApiError as e:
            logger.error(f"Slack authentication failed: {e}")
            raise ValueError(f"Slack authentication failed: {e}")
    
    def send_message(
        self, 
        text: str, 
        channel: Optional[str] = None, 
        blocks: Optional[List[Dict]] = None,
        thread_ts: Optional[str] = None,
        requirement_id: Optional[str] = None,
        pr_number: Optional[int] = None,
    ) -> SlackMessage:
        """Send a message to Slack.
        
        Args:
            text: Message text
            channel: Channel ID to send the message to. If not provided, will use the default channel.
            blocks: Message blocks (for rich formatting)
            thread_ts: Thread timestamp to reply to
            requirement_id: Related requirement ID
            pr_number: Related PR number
            
        Returns:
            SlackMessage: The sent message
        """
        channel_id = channel or self.channel
        if not channel_id:
            raise ValueError("Channel ID not provided")
        
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=text,
                blocks=blocks,
                thread_ts=thread_ts,
            )
            
            message = SlackMessage(
                id=response["ts"],
                channel=channel_id,
                text=text,
                user=response["message"]["user"],
                timestamp=response["ts"],
                requirement_id=requirement_id,
                pr_number=pr_number,
            )
            
            logger.info(f"Message sent to Slack: {message.id}")
            return message
        
        except SlackApiError as e:
            logger.error(f"Error sending message to Slack: {e}")
            raise ValueError(f"Error sending message to Slack: {e}")
    
    def send_requirement(self, requirement: Requirement, channel: Optional[str] = None) -> SlackMessage:
        """Send a requirement to Slack.
        
        Args:
            requirement: Requirement to send
            channel: Channel ID to send the message to. If not provided, will use the default channel.
            
        Returns:
            SlackMessage: The sent message
        """
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Requirement: {requirement.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": requirement.description
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Source:* {requirement.source_document}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Section:* {requirement.section}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Status:* {requirement.status}"
                    }
                ]
            },
            {
                "type": "divider"
            }
        ]
        
        # If Codegen user ID is provided, mention them
        text = f"New requirement: {requirement.title}"
        if self.codegen_user_id:
            text = f"<@{self.codegen_user_id}> {text}"
        
        return self.send_message(
            text=text,
            channel=channel,
            blocks=blocks,
            requirement_id=requirement.id,
        )
    
    def send_pr_review_notification(self, pr_review: PRReview, channel: Optional[str] = None) -> SlackMessage:
        """Send a PR review notification to Slack.
        
        Args:
            pr_review: PR review to send
            channel: Channel ID to send the message to. If not provided, will use the default channel.
            
        Returns:
            SlackMessage: The sent message
        """
        # Create blocks for the message
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"PR Review: {pr_review.title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Repository:* {pr_review.repository}\n*PR Number:* {pr_review.pr_number}\n*Author:* {pr_review.author}\n*Status:* {pr_review.status}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Review Result:* {pr_review.review_result}"
                }
            }
        ]
        
        # Add requirements met
        if pr_review.requirements_met:
            requirements_met_text = "\n".join([f"• {req}" for req in pr_review.requirements_met])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Requirements Met:*\n{requirements_met_text}"
                }
            })
        
        # Add requirements not met
        if pr_review.requirements_not_met:
            requirements_not_met_text = "\n".join([f"• {req}" for req in pr_review.requirements_not_met])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Requirements Not Met:*\n{requirements_not_met_text}"
                }
            })
        
        # Add review comments
        if pr_review.review_comments:
            comments_text = "\n".join([f"• {comment}" for comment in pr_review.review_comments])
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Review Comments:*\n{comments_text}"
                }
            })
        
        blocks.append({
            "type": "divider"
        })
        
        return self.send_message(
            text=f"PR Review: {pr_review.title} - {pr_review.review_result}",
            channel=channel,
            blocks=blocks,
            pr_number=pr_review.pr_number,
        )
    
    def get_messages(self, channel: Optional[str] = None, limit: int = 100) -> List[Dict]:
        """Get messages from a Slack channel.
        
        Args:
            channel: Channel ID to get messages from. If not provided, will use the default channel.
            limit: Maximum number of messages to retrieve
            
        Returns:
            List[Dict]: List of messages
        """
        channel_id = channel or self.channel
        if not channel_id:
            raise ValueError("Channel ID not provided")
        
        try:
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit,
            )
            return response["messages"]
        
        except SlackApiError as e:
            logger.error(f"Error getting messages from Slack: {e}")
            raise ValueError(f"Error getting messages from Slack: {e}")
