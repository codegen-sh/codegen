"""Agent implementation."""

import logging
from typing import Any, Dict, List, Optional, Sequence, Union

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from agentgen.backend.agents.utils import AgentConfig
from agentgen.backend.extensions.langchain.llm import LLM
from agentgen.backend.extensions.langchain.prompts import REASONER_SYSTEM_MESSAGE
from agentgen.backend.extensions.langchain.tools import (
    CreateFileTool,
    DeleteFileTool,
    GlobalReplacementEditTool,
    ListDirectoryTool,
    MoveSymbolTool,
    ReflectionTool,
    RelaceEditTool,
    RenameFileTool,
    ReplacementEditTool,
    RevealSymbolTool,
    RipGrepTool,
    SearchFilesByNameTool,
    ViewFileTool,
)

from .graph import create_react_agent

if TYPE_CHECKING:
    from codegen import Codebase


def create_codebase_agent(
    codebase: "Codebase",
    model_provider: str = "anthropic",
    model_name: str = "claude-3-7-sonnet-latest",
    system_message: SystemMessage = SystemMessage(REASONER_SYSTEM_MESSAGE),
    memory: bool = True,
    debug: bool = False,
    additional_tools: list[BaseTool] | None = None,
    config: AgentConfig | None = None,
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

    # Initialize default tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        RipGrepTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
        RenameFileTool(codebase),
        ReflectionTool(codebase),
        SearchFilesByNameTool(codebase),
        GlobalReplacementEditTool(codebase),
    ]

    if additional_tools:
        # Get names of additional tools
        additional_names = {t.get_name() for t in additional_tools}
        # Keep only tools that don't have matching names in additional_tools
        tools = [t for t in tools if t.get_name() not in additional_names]
        tools.extend(additional_tools)

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, system_message=system_message, checkpointer=memory, debug=debug, config=config)


def create_chat_agent(
    codebase: "Codebase",
    model_provider: str = "anthropic",
    model_name: str = "claude-3-5-sonnet-latest",
    system_message: SystemMessage = SystemMessage(REASONER_SYSTEM_MESSAGE),
    memory: bool = True,
    debug: bool = False,
    additional_tools: list[BaseTool] | None = None,
    config: dict[str, Any] | None = None,
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

    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        RipGrepTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
        RenameFileTool(codebase),
        MoveSymbolTool(codebase),
        RevealSymbolTool(codebase),
        RelaceEditTool(codebase),
    ]

    if additional_tools:
        tools.extend(additional_tools)

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, system_message=system_message, checkpointer=memory, debug=debug, config=config)


def create_codebase_inspector_agent(
    codebase: "Codebase",
    model_provider: str = "openai",
    model_name: str = "gpt-4o",
    system_message: SystemMessage = SystemMessage(REASONER_SYSTEM_MESSAGE),
    memory: bool = True,
    debug: bool = True,
    config: dict[str, Any] | None = None,
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
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        RipGrepTool(codebase),
        DeleteFileTool(codebase),
        RevealSymbolTool(codebase),
    ]

    memory = MemorySaver() if memory else None
    return create_react_agent(model=llm, tools=tools, system_message=system_message, checkpointer=memory, debug=debug, config=config)


def create_agent_with_tools(
    tools: list[BaseTool],
    model_provider: str = "openai",
    model_name: str = "gpt-4o",
    system_message: SystemMessage = SystemMessage(REASONER_SYSTEM_MESSAGE),
    memory: bool = True,
    debug: bool = True,
    config: dict[str, Any] | None = None,
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

    return create_react_agent(model=llm, tools=tools, system_message=system_message, checkpointer=memory, debug=debug, config=config)
