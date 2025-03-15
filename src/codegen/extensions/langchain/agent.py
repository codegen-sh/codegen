"""Demo implementation of an agent with Codegen tools."""

from typing import TYPE_CHECKING, Any, Optional

from langchain.tools import BaseTool
from langchain_core.messages import SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph

from codegen.agents.utils import AgentConfig
from codegen.extensions.langchain.llm import LLM
from codegen.extensions.langchain.prompts import REASONER_SYSTEM_MESSAGE
from codegen.extensions.langchain.tools import (
    CreateFileTool,
    DeleteFileTool,
    LinearCommentOnIssueTool,
    LinearCreateIssueTool,
    LinearGetIssueCommentsTool,
    LinearGetIssueTool,
    LinearGetTeamsTool,
    LinearSearchIssuesTool,
    ListDirectoryTool,
    MoveSymbolTool,
    ReflectionTool,
    RelaceEditTool,
    RenameFileTool,
    ReplacementEditTool,
    RevealSymbolTool,
    SearchTool,
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
    additional_tools: Optional[list[BaseTool]] = None,
    config: Optional[AgentConfig] = None,
    **kwargs,
) -> CompiledGraph:
    """Create an agent with all codebase tools.

    Args:
        codebase: The codebase to operate on
        model_provider: The model provider to use ("anthropic" or "openai")
        model_name: Name of the model to use
        system_message: Custom system message to use
        memory: Whether to enable memory/checkpointing
        debug: Whether to enable debug mode
        additional_tools: Optional additional tools to include
        **kwargs: Additional LLM configuration options

    Returns:
        Compiled langgraph agent
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    # Initialize Linear client if environment variables are set
    linear_client = None
    linear_tools = []
    try:
        from codegen.extensions.linear.linear_client import LinearClient

        linear_client = LinearClient()
        # Add Linear tools
        linear_tools = [
            LinearCreateIssueTool(linear_client),
            LinearGetIssueTool(linear_client),
            LinearSearchIssuesTool(linear_client),
            LinearCommentOnIssueTool(linear_client),
            LinearGetIssueCommentsTool(linear_client),
            LinearGetTeamsTool(linear_client),
        ]
    except (ImportError, ValueError):
        # Linear client not available or not configured
        pass

    # Core codebase tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
        RenameFileTool(codebase),
        ReplacementEditTool(codebase),
        RelaceEditTool(codebase),
        ReflectionTool(codebase),
    ]

    # Add Linear tools if available
    if linear_tools:
        tools.extend(linear_tools)

    # Add additional tools if provided
    if additional_tools:
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
    additional_tools: Optional[list[BaseTool]] = None,
    config: Optional[dict[str, Any]] = None,  # over here you can pass in the max length of the number of messages
    **kwargs,
) -> CompiledGraph:
    """Create an agent with chat-focused tools.

    Args:
        codebase: The codebase to operate on
        model_provider: The model provider to use ("anthropic" or "openai")
        model_name: Name of the model to use
        system_message: Custom system message to use
        memory: Whether to enable memory/checkpointing
        debug: Whether to enable debug mode
        additional_tools: Optional additional tools to include
        **kwargs: Additional LLM configuration options

    Returns:
        Compiled langgraph agent
    """
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    # Initialize Linear client if environment variables are set
    linear_client = None
    linear_tools = []
    try:
        from codegen.extensions.linear.linear_client import LinearClient

        linear_client = LinearClient()
        # Add Linear tools
        linear_tools = [
            LinearCreateIssueTool(linear_client),
            LinearGetIssueTool(linear_client),
            LinearSearchIssuesTool(linear_client),
            LinearCommentOnIssueTool(linear_client),
            LinearGetIssueCommentsTool(linear_client),
            LinearGetTeamsTool(linear_client),
        ]
    except (ImportError, ValueError):
        # Linear client not available or not configured
        pass

    # Core codebase tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
        RenameFileTool(codebase),
        MoveSymbolTool(codebase),
        RevealSymbolTool(codebase),
        RelaceEditTool(codebase),
    ]

    # Add Linear tools if available
    if linear_tools:
        tools.extend(linear_tools)

    # Add additional tools if provided
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
    config: Optional[dict[str, Any]] = None,
    **kwargs,
) -> CompiledGraph:
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
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
    config: Optional[dict[str, Any]] = None,
    **kwargs,
) -> CompiledGraph:
    llm = LLM(model_provider=model_provider, model_name=model_name, **kwargs)

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, system_message=system_message, checkpointer=memory, debug=debug, config=config)
