from typing import List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime

# Base dataclass for all message types
@dataclass
class BaseMessage:
    """Base class for all message types."""
    type: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    content: str = ""

@dataclass
class UserMessage(BaseMessage):
    """Represents a message from the user."""
    type: str = field(default="user")

@dataclass
class SystemMessageData(BaseMessage):
    """Represents a system message."""
    type: str = field(default="system")

@dataclass
class ToolCall:
    """Represents a tool call within an assistant message."""
    name: Optional[str] = None
    arguments: Optional[str] = None
    id: Optional[str] = None

@dataclass
class AssistantMessage(BaseMessage):
    """Represents a message from the assistant."""
    type: str = field(default="assistant")
    tool_calls: List[ToolCall] = field(default_factory=list)

@dataclass
class ToolMessageData(BaseMessage):
    """Represents a tool response message."""
    type: str = field(default="tool")
    tool_name: Optional[str] = None
    tool_response: Optional[str] = None
    tool_id: Optional[str] = None

@dataclass
class FunctionMessageData(BaseMessage):
    """Represents a function message."""
    type: str = field(default="function")

@dataclass
class UnknownMessage(BaseMessage):
    """Represents an unknown message type."""
    type: str = field(default="unknown") 

type AgentRunMessage = Union[UserMessage, SystemMessageData, AssistantMessage, ToolMessageData, FunctionMessageData, UnknownMessage]