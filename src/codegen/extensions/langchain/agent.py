"""Demo implementation of an agent with Codegen tools."""

from typing import Optional

from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph
from langgraph.prebuilt import create_react_agent

from codegen.extensions.tools.tools_client import (
    get_tools,
)
from codegen.runner.clients.sandbox_client import RemoteSandboxClient

from .llm import LLM
from .prompts import REASONER_SYSTEM_MESSAGE


def create_codebase_agent(
    codebase_client: RemoteSandboxClient,
    model_provider: str = "anthropic",
    model_name: str = "claude-3-5-sonnet-latest",
    system_message: SystemMessage = SystemMessage(REASONER_SYSTEM_MESSAGE),
    memory: bool = True,
    debug: bool = False,
    additional_tools: Optional[list[BaseTool]] = None,
    **kwargs,
) -> CompiledGraph:
    """Create an agent with all codebase tools.

    Args:
        codebase: The codebase to operate on
        model_provider: The model provider to use ("anthropic" or "openai")
        model_name: Name of the model to use
        verbose: Whether to print agent's thought process (default: True)
        chat_history: Optional list of messages to initialize chat history with
        **kwargs: Additional LLM configuration options. Supported options:
            - temperature: Temperature parameter (0-1)
            - top_p: Top-p sampling parameter (0-1)
            - top_k: Top-k sampling parameter (>= 1)
            - max_tokens: Maximum number of tokens to generate

    Returns:
        Initialized agent with message history
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)
    tools = get_tools(codebase_client)

    # Add additional tools if provided
    if additional_tools:
        tools.extend(additional_tools)

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, prompt=system_message, checkpointer=memory, debug=debug)


def create_codebase_inspector_agent(
    codebase_client: RemoteSandboxClient,
    model_provider: str = "openai",
    model_name: str = "gpt-4o",
    system_message: SystemMessage = SystemMessage(REASONER_SYSTEM_MESSAGE),
    memory: bool = True,
    debug: bool = True,
    **kwargs,
) -> CompiledGraph:
    """Create an inspector agent with read-only codebase tools.

    Args:
        codebase: The codebase to operate on
        model_provider: The model provider to use ("anthropic" or "openai")
        model_name: Name of the model to use
        system_message: Custom system message to use (defaults to standard reasoner message)
        memory: Whether to enable memory/checkpointing
        **kwargs: Additional LLM configuration options

    Returns:
        Compiled langgraph agent
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    # Get read-only codebase tools
    tools = get_tools(codebase_client)

    memory = MemorySaver() if memory else None
    return create_react_agent(model=llm, tools=tools, prompt=system_message, checkpointer=memory, debug=debug)


def create_agent_with_tools(
    tools: list[BaseTool],
    model_provider: str = "openai",
    model_name: str = "gpt-4o",
    system_message: SystemMessage = SystemMessage(REASONER_SYSTEM_MESSAGE),
    memory: bool = True,
    debug: bool = True,
    **kwargs,
) -> CompiledGraph:
    """Create an agent with a specific set of tools.

    Args:
        codebase: The codebase to operate on
        tools: List of tools to provide to the agent
        model_provider: The model provider to use ("anthropic" or "openai")
        model_name: Name of the model to use
        system_message: Custom system message to use (defaults to standard reasoner message)
        memory: Whether to enable memory/checkpointing
        **kwargs: Additional LLM configuration options. Supported options:
            - temperature: Temperature parameter (0-1)
            - top_p: Top-p sampling parameter (0-1)
            - top_k: Top-k sampling parameter (>= 1)
            - max_tokens: Maximum number of tokens to generate

    Returns:
        Compiled langgraph agent
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, prompt=system_message, checkpointer=memory, debug=debug)
