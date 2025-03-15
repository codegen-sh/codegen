"""Demo implementation of an agent with Codegen tools."""

import uuid
from typing import Annotated, Any, Literal, Optional, Union

import anthropic
import openai
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START
from langgraph.graph.state import CompiledGraph, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.pregel import RetryPolicy

from codegen.agents.utils import AgentConfig
from codegen.extensions.langchain.llm import LLM
from codegen.extensions.langchain.prompts import SUMMARIZE_CONVERSATION_PROMPT
from codegen.extensions.langchain.utils.utils import get_max_model_input_tokens


def manage_messages(existing: list[AnyMessage], updates: Union[list[AnyMessage], dict]) -> list[AnyMessage]:
    """Custom reducer for managing message history with summarization.

    Args:
        existing: Current list of messages
        updates: Either new messages to append or a dict specifying how to update messages

    Returns:
        Updated list of messages
    """
    if isinstance(updates, list):
        # Ensure all messages have IDs
        for msg in existing + updates:
            if not hasattr(msg, "id") or msg.id is None:
                msg.id = str(uuid.uuid4())

        # Create a map of existing messages by ID
        existing_by_id = {msg.id: i for i, msg in enumerate(existing)}

        # Start with copy of existing messages
        result = existing.copy()

        # Update or append new messages
        for msg in updates:
            if msg.id in existing_by_id:
                # Update existing message
                result[existing_by_id[msg.id]] = msg
            else:
                # Append new message
                result.append(msg)

        return result

    if isinstance(updates, dict):
        if updates.get("type") == "summarize":
            # Create summary message and mark it with additional_kwargs
            summary_msg = AIMessage(
                content=f"""Here is a summary of the conversation
            from a previous timestep to aid for the continuing conversation: \n{updates["summary"]}\n\n""",
                additional_kwargs={"is_summary": True},  # Use additional_kwargs for custom metadata
            )
            summary_msg.id = str(uuid.uuid4())
            updates["tail"][-1].additional_kwargs["just_summarized"] = True
            result = updates["head"] + [summary_msg] + updates["tail"]
            return result

    return existing


class GraphState(dict[str, Any]):
    """State of the graph."""

    query: str
    final_answer: str
    messages: Annotated[list[AnyMessage], manage_messages]


class AgentGraph:
    """Main graph class for the agent."""

    def __init__(self, model: "LLM", tools: list[BaseTool], system_message: SystemMessage, config: AgentConfig | None = None):
        self.model = model.bind_tools(tools)
        self.tools = tools
        self.system_message = system_message
        self.config = config
        self.max_messages = config.get("max_messages", 100) if config else 100
        self.keep_first_messages = config.get("keep_first_messages", 1) if config else 1

    # =================================== NODES ====================================

    # Reasoner node
    def reasoner(self, state: GraphState) -> dict[str, Any]:
        new_turn = len(state["messages"]) == 0 or isinstance(state["messages"][-1], AIMessage)
        messages = state["messages"]

        if new_turn:
            query = state["query"]
            messages.append(HumanMessage(content=query))

        result = self.model.invoke([self.system_message, *messages])
        if isinstance(result, AIMessage):
            updated_messages = [*messages, result]
            return {"messages": updated_messages, "final_answer": result.content}

        updated_messages = [*messages, result]
        return {"messages": updated_messages}

    def summarize_conversation(self, state: GraphState):
        """Summarize conversation while preserving key context and recent messages."""
        messages = state["messages"]
        keep_first = self.keep_first_messages
        target_size = len(messages) // 2
        messages_from_tail = target_size - keep_first

        head = messages[:keep_first]
        tail = messages[-messages_from_tail:]
        to_summarize = messages[: len(messages) - messages_from_tail]

        # Handle tool message pairing at truncation point
        truncation_idx = len(messages) - messages_from_tail
        if truncation_idx > 0 and isinstance(messages[truncation_idx], ToolMessage):
            # Keep the AI message right before it
            tail = [messages[truncation_idx - 1], *tail]

        # Skip if nothing to summarize
        if not to_summarize:
            return state

        # Define constants
        HEADER_WIDTH = 40
        HEADER_TYPES = {"human": "HUMAN", "ai": "AI", "summary": "SUMMARY FROM PREVIOUS TIMESTEP", "tool_call": "TOOL CALL", "tool_response": "TOOL RESPONSE"}

        def format_header(header_type: str) -> str:
            """Format message header with consistent padding.

            Args:
                header_type: Type of header to format (must be one of HEADER_TYPES)

            Returns:
                Formatted header string with padding
            """
            header = HEADER_TYPES[header_type]
            padding = "=" * ((HEADER_WIDTH - len(header)) // 2)
            return f"{padding} {header} {padding}\n"

        # Format messages with appropriate headers
        formatted_messages = []
        for msg in to_summarize:  # No need for slice when iterating full list
            if isinstance(msg, HumanMessage):
                formatted_messages.append(format_header("human") + msg.content)
            elif isinstance(msg, AIMessage):
                # Check for summary message using additional_kwargs
                if msg.additional_kwargs.get("is_summary"):
                    formatted_messages.append(format_header("summary") + msg.content)
                elif isinstance(msg.content, list) and len(msg.content) > 0 and isinstance(msg.content[0], dict):
                    for item in msg.content:  # No need for slice when iterating full list
                        if item.get("type") == "text":
                            formatted_messages.append(format_header("ai") + item["text"])
                        elif item.get("type") == "tool_use":
                            formatted_messages.append(format_header("tool_call") + f"Tool: {item['name']}\nInput: {item['input']}")
                else:
                    formatted_messages.append(format_header("ai") + msg.content)
            elif isinstance(msg, ToolMessage):
                formatted_messages.append(format_header("tool_response") + msg.content)

        conversation = "\n".join(formatted_messages)  # No need for slice when joining full list

        summary_llm = LLM(
            model_provider="anthropic",
            model_name="claude-3-5-sonnet-latest",
            temperature=0.3,
        )

        chain = ChatPromptTemplate.from_template(SUMMARIZE_CONVERSATION_PROMPT) | summary_llm
        new_summary = chain.invoke({"conversation": conversation}).content

        return {"messages": {"type": "summarize", "summary": new_summary, "tail": tail, "head": head}}

    # =================================== EDGE CONDITIONS ====================================
    def should_continue(self, state: GraphState) -> Literal["tools", "summarize_conversation", END]:
        messages = state["messages"]
        last_message = messages[-1]
        just_summarized = last_message.additional_kwargs.get("just_summarized")
        curr_input_tokens = last_message.usage_metadata["input_tokens"]
        max_input_tokens = get_max_model_input_tokens(self.model)

        # Summarize if the number of messages passed in exceeds the max_messages threshold (default 100)
        if len(messages) > self.max_messages:
            return "summarize_conversation"

        # Summarize if the last message exceeds the max input tokens of the model - 10000 tokens
        elif isinstance(last_message, AIMessage) and not just_summarized and curr_input_tokens > (max_input_tokens - 10000):
            return "summarize_conversation"

        elif hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return END

    # =================================== COMPILE GRAPH ====================================
    def create(self, checkpointer: Optional[MemorySaver] = None, debug: bool = False) -> CompiledGraph:
        """Create and compile the graph."""
        builder = StateGraph(GraphState)

        # the retry policy has an initial interval, a backoff factor, and a max interval of controlling the
        # amount of time between retries
        retry_policy = RetryPolicy(
            retry_on=[anthropic.RateLimitError, openai.RateLimitError, anthropic.InternalServerError, anthropic.BadRequestError],
            max_attempts=10,
            initial_interval=30.0,  # Start with 30 second wait
            backoff_factor=2,  # Double the wait time each retry
            max_interval=1000.0,  # Cap at 1000 second max wait
            jitter=True,
        )

        # Custom error handler for tool validation errors
        def handle_tool_errors(exception):
            error_msg = str(exception)

            # Extract tool name and input from the exception if possible
            tool_name = "unknown"
            tool_input = {}

            # Helper function to get field descriptions from any tool
            def get_field_descriptions(tool_obj):
                field_descriptions = {}
                if not tool_obj or not hasattr(tool_obj, "args_schema"):
                    return field_descriptions

                try:
                    # Get all field descriptions from the tool
                    schema_cls = tool_obj.args_schema

                    # Handle Pydantic v2
                    if hasattr(schema_cls, "model_fields"):
                        for field_name, field in schema_cls.model_fields.items():
                            field_descriptions[field_name] = field.description or f"Required parameter for {tool_obj.name}"

                    # Handle Pydantic v1 with warning suppression
                    elif hasattr(schema_cls, "__fields__"):
                        import warnings

                        with warnings.catch_warnings():
                            warnings.filterwarnings("ignore", category=DeprecationWarning)
                            for field_name, field in schema_cls.__fields__.items():
                                field_descriptions[field_name] = field.field_info.description or f"Required parameter for {tool_obj.name}"
                except Exception:
                    pass

                return field_descriptions

            # Try to extract tool name and input from the exception
            import re

            tool_match = re.search(r"for (\w+)Input", error_msg)
            if tool_match:
                # Get the extracted name but preserve original case by finding the matching tool
                extracted_name = tool_match.group(1).lower()
                for t in self.tools:
                    if t.name.lower() == extracted_name:
                        tool_name = t.name  # Use the original case from the tool
                        break

            # Try to extract the input values
            input_match = re.search(r"input_value=(\{.*?\})", error_msg)
            if input_match:
                input_str = input_match.group(1)
                # Simple parsing of the dict-like string
                try:
                    # Clean up the string to make it more parseable
                    input_str = input_str.replace("'", '"')
                    import json

                    tool_input = json.loads(input_str)
                except Exception as e:
                    print(f"Failed to parse tool input: {e}")

            # Handle validation errors with more helpful messages
            if "validation error" in error_msg.lower():
                # Find the tool in our tools list to get its schema
                tool = next((t for t in self.tools if t.name == tool_name), None)

                # If we couldn't find the tool by extracted name, try to find it by looking at all tools
                if tool is None:
                    # Try to extract tool name from the error message
                    for t in self.tools:
                        if t.name.lower() in error_msg.lower():
                            tool = t
                            tool_name = t.name
                            break

                    # If still not found, check if any tool's schema name matches
                    if tool is None:
                        for t in self.tools:
                            if hasattr(t, "args_schema") and t.args_schema.__name__.lower() in error_msg.lower():
                                tool = t
                                tool_name = t.name
                                break

                # Check for type errors
                type_errors = []
                if "type_error" in error_msg.lower():
                    import re

                    # Try to extract type error information
                    type_error_matches = re.findall(r"'(\w+)'.*?type_error\.(.*?)(?:;|$)", error_msg, re.IGNORECASE)
                    for field_name, error_type in type_error_matches:
                        if "json" in error_type:
                            type_errors.append(f"'{field_name}' must be a string, not a JSON object or dictionary")
                        elif "str_type" in error_type:
                            type_errors.append(f"'{field_name}' must be a string")
                        elif "int_type" in error_type:
                            type_errors.append(f"'{field_name}' must be an integer")
                        elif "bool_type" in error_type:
                            type_errors.append(f"'{field_name}' must be a boolean")
                        elif "list_type" in error_type:
                            type_errors.append(f"'{field_name}' must be a list")
                        else:
                            type_errors.append(f"'{field_name}' has an incorrect type")

                if type_errors:
                    errors_str = "\n- ".join(type_errors)
                    return f"Error using {tool_name} tool: Parameter type errors:\n- {errors_str}\n\nYou provided: {tool_input}\n\nPlease try again with the correct parameter types."

                # Get missing fields by comparing tool input with required fields
                missing_fields = []
                if tool and hasattr(tool, "args_schema"):
                    try:
                        # Get the schema class
                        schema_cls = tool.args_schema

                        # Handle Pydantic v2 (preferred) or v1 with warning suppression
                        if hasattr(schema_cls, "model_fields"):  # Pydantic v2
                            for field_name, field in schema_cls.model_fields.items():
                                # Check if field is required and missing from input
                                if field.is_required() and field_name not in tool_input:
                                    missing_fields.append(field_name)
                        else:  # Pydantic v1 with warning suppression
                            import warnings

                            with warnings.catch_warnings():
                                warnings.filterwarnings("ignore", category=DeprecationWarning)
                                for field_name, field in schema_cls.__fields__.items():
                                    # Check if field is required and missing from input
                                    if field.required and field_name not in tool_input:
                                        missing_fields.append(field_name)
                    except Exception as e:
                        # If we can't extract schema info, we'll fall back to regex
                        pass

                # If we couldn't get missing fields from schema, try to extract from error message
                if not missing_fields:
                    # Extract the missing field name if possible using regex
                    import re

                    field_matches = re.findall(r"'(\w+)'(?:\s+|.*?)field required", error_msg, re.IGNORECASE)
                    if field_matches:
                        missing_fields = field_matches
                    else:
                        # Try another pattern
                        field_match = re.search(r"(\w+)\s+Field required", error_msg)
                        if field_match:
                            missing_fields = [field_match.group(1)]

                # If we have identified missing fields, create a helpful error message
                if missing_fields:
                    fields_str = ", ".join([f"'{f}'" for f in missing_fields])

                    # Get tool documentation if available
                    tool_docs = ""
                    if tool:
                        if hasattr(tool, "description") and tool.description:
                            tool_docs = f"\nTool description: {tool.description}\n"

                        # Try to get parameter descriptions from the schema
                        param_docs = []
                        try:
                            # Get all field descriptions from the tool
                            field_descriptions = get_field_descriptions(tool)

                            # Add descriptions for missing fields
                            for field_name in missing_fields:
                                if field_name in field_descriptions:
                                    param_docs.append(f"- {field_name}: {field_descriptions[field_name]}")
                                else:
                                    param_docs.append(f"- {field_name}: Required parameter")

                            if param_docs:
                                tool_docs += "\nParameter descriptions:\n" + "\n".join(param_docs)
                        except Exception:
                            # Fallback to simple parameter list
                            param_docs = [f"- {field}: Required parameter" for field in missing_fields]
                            if param_docs:
                                tool_docs += "\nMissing parameters:\n" + "\n".join(param_docs)

                    # Add usage examples for common tools
                    example = ""
                    if tool_name == "create_file":
                        example = "\nExample: create_file(filepath='path/to/file.py', content='print(\"Hello world\")')"
                    elif tool_name == "replace_edit":
                        example = "\nExample: replace_edit(filepath='path/to/file.py', old_text='def old_function()', new_text='def new_function()')"
                    elif tool_name == "view_file":
                        example = "\nExample: view_file(filepath='path/to/file.py')"
                    elif tool_name == "search":
                        example = "\nExample: search(query='function_name', file_extensions=['.py'])"

                    return (
                        f"Error using {tool_name} tool: Missing required parameter(s): {fields_str}\n\nYou provided: {tool_input}\n{tool_docs}{example}\nPlease try again with all required parameters."
                    )

                # Common error patterns for specific tools (as fallback)
                if tool_name == "create_file":
                    if "content" not in tool_input:
                        return (
                            "Error: When using the create_file tool, you must provide both 'filepath' and 'content' parameters.\n"
                            "The 'content' parameter is missing. Please try again with both parameters.\n\n"
                            "Example: create_file(filepath='path/to/file.py', content='print(\"Hello world\")')"
                        )
                    elif "filepath" not in tool_input:
                        return (
                            "Error: When using the create_file tool, you must provide both 'filepath' and 'content' parameters.\n"
                            "The 'filepath' parameter is missing. Please try again with both parameters.\n\n"
                            "Example: create_file(filepath='path/to/file.py', content='print(\"Hello world\")')"
                        )

                elif tool_name == "replace_edit":
                    if "filepath" not in tool_input:
                        return (
                            "Error: When using the replace_edit tool, you must provide 'filepath', 'old_text', and 'new_text' parameters.\n"
                            "The 'filepath' parameter is missing. Please try again with all required parameters."
                        )
                    elif "old_text" not in tool_input:
                        return (
                            "Error: When using the replace_edit tool, you must provide 'filepath', 'old_text', and 'new_text' parameters.\n"
                            "The 'old_text' parameter is missing. Please try again with all required parameters."
                        )
                    elif "new_text" not in tool_input:
                        return (
                            "Error: When using the replace_edit tool, you must provide 'filepath', 'old_text', and 'new_text' parameters.\n"
                            "The 'new_text' parameter is missing. Please try again with all required parameters."
                        )

                # Generic validation error with better formatting
                if tool:
                    return (
                        f"Error using {tool_name} tool: {error_msg}\n\n"
                        f"You provided these parameters: {tool_input}\n\n"
                        f"Please check the tool's required parameters and try again with all required fields."
                    )
                else:
                    # If we couldn't identify the tool, list all available tools
                    available_tools = "\n".join([f"- {t.name}" for t in self.tools])
                    return f"Error: Could not identify the tool you're trying to use.\n\nAvailable tools:\n{available_tools}\n\nPlease use one of the available tools with the correct parameters."

            # For other types of errors
            return f"Error executing tool: {error_msg}\n\nPlease check your tool usage and try again with the correct parameters."

        # Add nodes
        builder.add_node("reasoner", self.reasoner, retry=retry_policy)
        builder.add_node("tools", ToolNode(self.tools, handle_tool_errors=handle_tool_errors), retry=retry_policy)
        builder.add_node("summarize_conversation", self.summarize_conversation, retry=retry_policy)

        # Add edges
        builder.add_edge(START, "reasoner")
        builder.add_edge("tools", "reasoner")
        builder.add_conditional_edges(
            "reasoner",
            self.should_continue,
        )
        builder.add_conditional_edges("summarize_conversation", self.should_continue)

        return builder.compile(checkpointer=checkpointer, debug=debug)


def create_react_agent(
    model: "LLM",
    tools: list[BaseTool],
    system_message: SystemMessage,
    checkpointer: Optional[MemorySaver] = None,
    debug: bool = False,
    config: Optional[dict[str, Any]] = None,
) -> CompiledGraph:
    """Create a reactive agent graph."""
    graph = AgentGraph(model, tools, system_message, config=config)
    return graph.create(checkpointer=checkpointer, debug=debug)
