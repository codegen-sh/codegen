"""
Slack integration module for the unified agent application.
This module provides functionality for interacting with Slack.
"""

import os
import logging
import threading
import time
from typing import Dict, List, Optional, Any, Callable, Union
import asyncio

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from .config import config

logger = logging.getLogger(__name__)

class SlackIntegration:
    """Slack integration for the unified agent application."""
    
    def __init__(self, bot_token: Optional[str] = None, app_token: Optional[str] = None, channel_id: Optional[str] = None):
        """Initialize the Slack integration."""
        self.bot_token = bot_token or config.slack.bot_token
        self.app_token = app_token or config.slack.app_token
        self.channel_id = channel_id or config.slack.channel_id
        
        self.client = WebClient(token=self.bot_token) if self.bot_token else None
        self.socket_mode_client = None
        self.event_handlers = {}
        self.running = False
        self.thread = None
    
    def connect(self) -> bool:
        """Connect to Slack."""
        if not self.bot_token or not self.app_token:
            logger.error("Slack bot token and app token are required")
            return False
        
        try:
            # Test the bot token
            self.client = WebClient(token=self.bot_token)
            auth_test = self.client.auth_test()
            if not auth_test["ok"]:
                logger.error(f"Failed to authenticate with Slack: {auth_test}")
                return False
            
            # Initialize the socket mode client
            self.socket_mode_client = SocketModeClient(
                app_token=self.app_token,
                web_client=self.client
            )
            
            # Set up the event handlers
            self.socket_mode_client.socket_mode_request_listeners.append(self._handle_socket_mode_request)
            
            return True
        except SlackApiError as e:
            logger.error(f"Failed to connect to Slack: {e}")
            return False
    
    def start(self) -> bool:
        """Start the Slack integration."""
        if not self.socket_mode_client:
            if not self.connect():
                return False
        
        if self.running:
            return True
        
        try:
            self.running = True
            self.thread = threading.Thread(target=self._run_socket_mode_client)
            self.thread.daemon = True
            self.thread.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start Slack integration: {e}")
            self.running = False
            return False
    
    def stop(self) -> None:
        """Stop the Slack integration."""
        self.running = False
        if self.socket_mode_client:
            self.socket_mode_client.close()
            self.socket_mode_client = None
        if self.thread:
            self.thread.join(timeout=1)
            self.thread = None
    
    def _run_socket_mode_client(self) -> None:
        """Run the socket mode client."""
        try:
            self.socket_mode_client.connect()
            while self.running:
                time.sleep(1)
        except Exception as e:
            logger.error(f"Error in socket mode client: {e}")
            self.running = False
    
    def _handle_socket_mode_request(self, client: SocketModeClient, request: SocketModeRequest) -> None:
        """Handle a socket mode request."""
        # Acknowledge the request
        response = SocketModeResponse(envelope_id=request.envelope_id)
        client.send_socket_mode_response(response)
        
        # Process the request
        if request.type == "events_api":
            event = request.payload.get("event", {})
            event_type = event.get("type")
            
            if event_type in self.event_handlers:
                for handler in self.event_handlers[event_type]:
                    try:
                        handler(event)
                    except Exception as e:
                        logger.error(f"Error in event handler for {event_type}: {e}")
    
    def register_event_handler(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> None:
        """Register an event handler."""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def send_message(self, text: str, channel: Optional[str] = None, thread_ts: Optional[str] = None, blocks: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """Send a message to a Slack channel."""
        if not self.client:
            logger.error("Slack client not initialized")
            return None
        
        channel_id = channel or self.channel_id
        if not channel_id:
            logger.error("Channel ID is required")
            return None
        
        try:
            response = self.client.chat_postMessage(
                channel=channel_id,
                text=text,
                thread_ts=thread_ts,
                blocks=blocks
            )
            return response
        except SlackApiError as e:
            logger.error(f"Failed to send message to Slack: {e}")
            return None
    
    def update_message(self, ts: str, text: str, channel: Optional[str] = None, blocks: Optional[List[Dict[str, Any]]] = None) -> Optional[Dict[str, Any]]:
        """Update a message in a Slack channel."""
        if not self.client:
            logger.error("Slack client not initialized")
            return None
        
        channel_id = channel or self.channel_id
        if not channel_id:
            logger.error("Channel ID is required")
            return None
        
        try:
            response = self.client.chat_update(
                channel=channel_id,
                ts=ts,
                text=text,
                blocks=blocks
            )
            return response
        except SlackApiError as e:
            logger.error(f"Failed to update message in Slack: {e}")
            return None
    
    def delete_message(self, ts: str, channel: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Delete a message from a Slack channel."""
        if not self.client:
            logger.error("Slack client not initialized")
            return None
        
        channel_id = channel or self.channel_id
        if not channel_id:
            logger.error("Channel ID is required")
            return None
        
        try:
            response = self.client.chat_delete(
                channel=channel_id,
                ts=ts
            )
            return response
        except SlackApiError as e:
            logger.error(f"Failed to delete message from Slack: {e}")
            return None
    
    def add_reaction(self, name: str, channel: str, timestamp: str) -> Optional[Dict[str, Any]]:
        """Add a reaction to a message."""
        if not self.client:
            logger.error("Slack client not initialized")
            return None
        
        try:
            response = self.client.reactions_add(
                name=name,
                channel=channel,
                timestamp=timestamp
            )
            return response
        except SlackApiError as e:
            logger.error(f"Failed to add reaction to message: {e}")
            return None
    
    def remove_reaction(self, name: str, channel: str, timestamp: str) -> Optional[Dict[str, Any]]:
        """Remove a reaction from a message."""
        if not self.client:
            logger.error("Slack client not initialized")
            return None
        
        try:
            response = self.client.reactions_remove(
                name=name,
                channel=channel,
                timestamp=timestamp
            )
            return response
        except SlackApiError as e:
            logger.error(f"Failed to remove reaction from message: {e}")
            return None
    
    def get_channel_history(self, channel: Optional[str] = None, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get the history of a Slack channel."""
        if not self.client:
            logger.error("Slack client not initialized")
            return None
        
        channel_id = channel or self.channel_id
        if not channel_id:
            logger.error("Channel ID is required")
            return None
        
        try:
            response = self.client.conversations_history(
                channel=channel_id,
                limit=limit
            )
            return response.get("messages", [])
        except SlackApiError as e:
            logger.error(f"Failed to get channel history from Slack: {e}")
            return None
    
    def get_thread_replies(self, thread_ts: str, channel: Optional[str] = None, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """Get the replies in a thread."""
        if not self.client:
            logger.error("Slack client not initialized")
            return None
        
        channel_id = channel or self.channel_id
        if not channel_id:
            logger.error("Channel ID is required")
            return None
        
        try:
            response = self.client.conversations_replies(
                channel=channel_id,
                ts=thread_ts,
                limit=limit
            )
            return response.get("messages", [])
        except SlackApiError as e:
            logger.error(f"Failed to get thread replies from Slack: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test the connection to Slack."""
        if not self.bot_token or not self.app_token:
            return False
        
        try:
            client = WebClient(token=self.bot_token)
            auth_test = client.auth_test()
            return auth_test["ok"]
        except SlackApiError:
            return False

# Global Slack integration instance
slack = SlackIntegration()