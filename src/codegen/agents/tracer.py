from collections.abc import Generator
from typing import Any, Optional

from langchain.schema import AIMessage, HumanMessage
from langchain.schema import FunctionMessage as LCFunctionMessage
from langchain.schema import SystemMessage as LCSystemMessage
from langchain_core.messages import ToolMessage as LCToolMessage

from .data import AssistantMessage, BaseMessage, FunctionMessageData, SystemMessageData, ToolCall, ToolMessageData, UnknownMessage, UserMessage
from .loggers import ExternalLogger


class MessageStreamTracer:
    def __init__(self, logger: Optional[ExternalLogger] = None):
        self.traces = []
        self.logger = logger

    def process_stream(self, message_stream: Generator) -> Generator:
        """Process the stream of messages from the LangGraph agent,
        extract structured data, and pass through the messages.
        """
        for chunk in message_stream:
            # Process the chunk
            structured_data = self.extract_structured_data(chunk)

            # Log the structured data
            if structured_data:
                self.traces.append(structured_data)

                # If there's an external logger, send the data there
                if self.logger:
                    self.logger.log(structured_data)

            # Pass through the chunk to maintain the original stream behavior
            yield chunk

    def extract_structured_data(self, chunk: dict[str, Any]) -> Optional[BaseMessage]:
        """Extract structured data from a message chunk.
        Returns None if the chunk doesn't contain useful information.
        Returns a BaseMessage subclass instance based on the message type.
        """
        # Get the messages from the chunk if available
        messages = chunk.get("messages", [])
        if not messages and isinstance(chunk, dict):
            # Sometimes the message might be in a different format
            for key, value in chunk.items():
                if isinstance(value, list) and all(hasattr(item, "type") for item in value if hasattr(item, "__dict__")):
                    messages = value
                    break

        if not messages:
            return None

        # Get the latest message
        latest_message = messages[-1] if messages else None

        if not latest_message:
            return None

        # Determine message type
        message_type = self._get_message_type(latest_message)
        content = self._get_message_content(latest_message)

        # Create the appropriate message type
        if message_type == "user":
            return UserMessage(type=message_type, content=content)
        elif message_type == "system":
            return SystemMessageData(type=message_type, content=content)
        elif message_type == "assistant":
            tool_calls_data = self._extract_tool_calls(latest_message)
            tool_calls = [ToolCall(name=tc.get("name"), arguments=tc.get("arguments"), id=tc.get("id")) for tc in tool_calls_data]
            return AssistantMessage(type=message_type, content=content, tool_calls=tool_calls)
        elif message_type == "tool":
            return ToolMessageData(type=message_type, content=content, tool_name=getattr(latest_message, "name", None), tool_response=content, tool_id=getattr(latest_message, "tool_call_id", None))
        elif message_type == "function":
            return FunctionMessageData(type=message_type, content=content)
        else:
            return UnknownMessage(type=message_type, content=content)

    def _get_message_type(self, message) -> str:
        """Determine the type of message."""
        if isinstance(message, HumanMessage):
            return "user"
        elif isinstance(message, AIMessage):
            return "assistant"
        elif isinstance(message, LCSystemMessage):
            return "system"
        elif isinstance(message, LCFunctionMessage):
            return "function"
        elif isinstance(message, LCToolMessage):
            return "tool"
        elif hasattr(message, "type") and message.type:
            return message.type
        else:
            return "unknown"

    def _get_message_content(self, message) -> str:
        """Extract content from a message."""
        if hasattr(message, "content"):
            return message.content
        elif hasattr(message, "message") and hasattr(message.message, "content"):
            return message.message.content
        else:
            return str(message)

    def _extract_tool_calls(self, message) -> list[dict[str, Any]]:
        """Extract tool calls from an assistant message."""
        tool_calls = []

        # Check different possible locations for tool calls
        if hasattr(message, "additional_kwargs") and "tool_calls" in message.additional_kwargs:
            raw_tool_calls = message.additional_kwargs["tool_calls"]
            for tc in raw_tool_calls:
                tool_calls.append({"name": tc.get("function", {}).get("name"), "arguments": tc.get("function", {}).get("arguments"), "id": tc.get("id")})

        # Also check for function_call which is used in some models
        elif hasattr(message, "additional_kwargs") and "function_call" in message.additional_kwargs:
            fc = message.additional_kwargs["function_call"]
            if isinstance(fc, dict):
                tool_calls.append(
                    {
                        "name": fc.get("name"),
                        "arguments": fc.get("arguments"),
                        "id": "function_call_1",  # Assigning a default ID
                    }
                )

        return tool_calls

    def get_traces(self) -> list[BaseMessage]:
        """Get all collected traces."""
        return self.traces

    def clear_traces(self) -> None:
        """Clear all traces."""
        self.traces = []
