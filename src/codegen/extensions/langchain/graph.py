"""Demo implementation of an agent with Codegen tools."""

import uuid
from typing import TYPE_CHECKING, Annotated, Any, Literal, Optional, Union

import anthropic
import openai
from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START
from langgraph.graph.state import CompiledGraph, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.pregel import RetryPolicy

from codegen.agents.utils import AgentConfig
from codegen.extensions.langchain.prompts import SUMMARIZE_CONVERSATION_PROMPT


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
            # Add summary message
            summary_msg = AIMessage(content=f"This next few sections contain a summary of the conversation: \n{updates['summary']}")
            summary_msg.id = str(uuid.uuid4())  # Ensure summary message has ID
            result = updates["head"] + [summary_msg] + updates["tail"]
            return result

    return existing


class GraphState(dict[str, Any]):
    """State of the graph."""

    summary: str
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
        keep_first = self.keep_first_messages  # Keep system prompt and initial user message
        target_size = self.max_messages // 2
        messages_from_tail = target_size - keep_first

        # If we don't have enough messages to require summarization
        if len(messages) <= self.max_messages:
            return state

        head = messages[:keep_first]  # gets first message  (human instruction)
        tail = messages[-messages_from_tail:]  # gets last 48 messages (default implementation with 100 max messages)
        to_summarize = messages[keep_first:-messages_from_tail]  # gets middle messages to summarize -> len(messages) - (len(tail) + len(head))

        # Skip if nothing to summarize
        if not to_summarize:
            return state

        summary = state.get("summary", "")
        summary_prompt = SUMMARIZE_CONVERSATION_PROMPT
        if summary:
            summary_prompt += f"\n\nPrevious summary: {summary}\n\nExtend this summary with the new conversation:"

        # Convert messages to string format for summarization
        conversation = "\n".join(f"{msg.type}: {msg.content}" for msg in to_summarize)

        messages_for_summary = [SystemMessage(content=summary_prompt), HumanMessage(content="Summarize the following conversation: \n\n" + conversation)]

        response = self.model.invoke(messages_for_summary)
        new_summary = response.content

        return {"messages": {"type": "summarize", "summary": new_summary, "tail": tail, "head": head}, "summary": new_summary}

    # =================================== EDGE CONDITIONS ====================================
    def should_continue(self, state: GraphState) -> Literal["tools", "summarize_conversation", END]:
        messages = state["messages"]
        last_message = messages[-1]

        # If the message count exceeds the limit, summarize before performing tool call
        if len(messages) > self.max_messages:
            return "summarize_conversation"

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"

        return END

    # =================================== COMPILE GRAPH ====================================
    def create(self, checkpointer: Optional[MemorySaver] = None, debug: bool = False) -> CompiledGraph:
        """Create and compile the graph."""
        builder = StateGraph(GraphState)

        # the retry policy has an initial interval, a backoff factor, and a max interval of controlling the
        # amount of time between retries
        retry_policy = RetryPolicy(
            retry_on=[anthropic.RateLimitError, openai.RateLimitError, anthropic.InternalServerError],
            max_attempts=10,
            initial_interval=30.0,  # Start with 30 second wait
            backoff_factor=2,  # Double the wait time each retry
            max_interval=1000.0,  # Cap at 1000 second max wait
            jitter=True,
        )

        # Add nodes
        builder.add_node("reasoner", self.reasoner, retry=retry_policy)
        builder.add_node("tools", ToolNode(self.tools), retry=retry_policy)
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


if TYPE_CHECKING:
    from codegen.extensions.langchain.llm import LLM
