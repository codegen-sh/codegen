"""Utility functions for agents."""

from typing import Any, Dict, Optional, TypedDict


class AgentConfig(TypedDict, total=False):
    """Configuration for an agent."""

    max_messages: int
    keep_first_messages: int


def get_config(config: Optional[Dict[str, Any]] = None) -> AgentConfig:
    """Get agent configuration with defaults.

    Args:
        config: Optional configuration dictionary

    Returns:
        Configuration with defaults applied
    """
    if config is None:
        config = {}

    return {
        "max_messages": config.get("max_messages", 100),
        "keep_first_messages": config.get("keep_first_messages", 1),
    }
