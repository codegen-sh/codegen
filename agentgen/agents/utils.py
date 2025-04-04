from typing import TypedDict


class AgentConfig(TypedDict, total=False):
    """Configuration options for the CodeAgent."""

    keep_first_messages: int  # Number of initial messages to keep during summarization
    max_messages: int  # Maximum number of messages before triggering summarization
