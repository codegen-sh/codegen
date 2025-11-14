"""Utility functions for Slack integration."""

import logging
from typing import Any, Dict, Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.INFO)


def safe_add_reaction(
    client: WebClient,
    channel: str,
    timestamp: str,
    name: str,
) -> dict[str, Any]:
    """Safely add a reaction to a Slack message, handling the case where the reaction already exists.

    Args:
        client: The Slack WebClient instance
        channel: The channel ID where the message is located
        timestamp: The timestamp of the message
        name: The name of the reaction emoji to add

    Returns:
        The response from the Slack API or an error response
    """
    try:
        return client.reactions_add(
            channel=channel,
            timestamp=timestamp,
            name=name,
        )
    except SlackApiError as e:
        # If the error is "already_reacted", just log it and continue
        if e.response["error"] == "already_reacted":
            logger.info(f"Reaction '{name}' already exists on message in channel {channel} at {timestamp}. Ignoring.")
            # Return a success response to prevent further error handling
            return {"ok": True, "already_exists": True}
        # For other errors, re-raise
        logger.exception(f"Error adding reaction: {e}")
        raise
