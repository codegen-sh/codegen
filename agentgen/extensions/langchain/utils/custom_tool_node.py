from typing import Any, Literal, Optional, Union

from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    ToolCall,
)
from langchain_core.stores import InMemoryBaseStore
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel


class CustomToolNode(ToolNode):
    """Extended ToolNode that detects truncated tool calls."""

    def _parse_input(
        self,
        input: Union[
            list[AnyMessage],
            dict[str, Any],
            BaseModel,
        ],
        store: Optional[InMemoryBaseStore],
    ) -> tuple[list[ToolCall], Literal["list", "dict", "tool_calls"]]:
        """Parse the input and check for truncated tool calls."""
        messages = input.get("messages", [])
        if isinstance(messages, list):
            if isinstance(messages[-1], AIMessage):
                response_metadata = messages[-1].response_metadata
                # Check if the stop reason is due to max tokens
                if response_metadata.get("stop_reason") == "max_tokens":
                    # Check if the response metadata contains usage information
                    if "usage" not in response_metadata or "output_tokens" not in response_metadata["usage"]:
                        msg = "Response metadata is missing usage information."
                        raise ValueError(msg)

                    output_tokens = response_metadata["usage"]["output_tokens"]
                    for tool_call in messages[-1].tool_calls:
                        if tool_call.get("name") == "create_file":
                            # Set the max tokens and max tokens reached flag in the store
                            store.mset([(tool_call["name"], {"max_tokens": output_tokens, "max_tokens_reached": True})])

        return super()._parse_input(input, store)
