"""Demo implementation of an agent with Codegen tools."""

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain.hub import pull
from langchain.tools import BaseTool
from langchain_anthropic import ChatAnthropic
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI

from codegen.sdk.core.codebase import Codebase

from .tools import (
    CreateFileTool,
    DeleteFileTool,
    EditFileTool,
    ListDirectoryTool,
    MoveSymbolTool,
    RenameFileTool,
    ReplacementEditTool,
    RevealSymbolTool,
    SearchTool,
    SemanticEditTool,
    ViewFileTool,
)


def create_codebase_agent(
    codebase: Codebase,
    model_name: str = "claude-3-5-sonnet-latest",
    temperature: float = 0,
    verbose: bool = True,
    chat_history: list[BaseMessage] = [],
) -> RunnableWithMessageHistory:
    """Create an agent with all codebase tools.

    Args:
        codebase: The codebase to operate on
        model_name: Name of the model to use (default: gpt-4)
        temperature: Model temperature (default: 0)
        verbose: Whether to print agent's thought process (default: True)

    Returns:
        Initialized agent with message history
    """
    # Initialize language model
    # llm = ChatOpenAI(
    #     model_name=model_name,
    #     temperature=temperature,
    # )

    llm = ChatAnthropic(
        model="claude-3-5-sonnet-latest",
        temperature=temperature,
    )

    # Get all codebase tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
        EditFileTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
        RenameFileTool(codebase),
        MoveSymbolTool(codebase),
        RevealSymbolTool(codebase),
        SemanticEditTool(codebase),
        ReplacementEditTool(codebase),
        # SemanticSearchTool(codebase),
        # =====[ Github Integration ]=====
        # Enable Github integration
        # GithubCreatePRTool(codebase),
        # GithubViewPRTool(codebase),
        # GithubCreatePRCommentTool(codebase),
        # GithubCreatePRReviewCommentTool(codebase),
    ]

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
            You are an expert software engineer with deep knowledge of code analysis, refactoring, and development best practices.
            You have access to a powerful set of tools from  codegen that allow you to analyze and modify codebases:

        Core Capabilities:
        1. Code Analysis & Navigation:
        - Search codebases using text or regex patterns
        - View file contents and metadata (functions, classes, imports)
        - Analyze code structure and dependencies
        - Reveal symbol definitions and usages

        2. File Operations:
        - View, create, edit, and delete files
        - Rename files while updating all imports
        - Move symbols between files
        - Commit changes to disk

        3. Semantic Editing:
        - Make precise, context-aware code edits
        - Analyze affected code structures
        - Preview changes before applying
        - Ensure code quality with linting

        4. Code Search:
        - Text-based and semantic search
        - Search within specific directories
        - Filter by file extensions
        - Get paginated results

        Best Practices:
        - Always analyze code structure before making changes
        - Preview edits to understand their impact
        - Update imports and dependencies when moving code
        - Use semantic edits for complex changes
        - Commit changes after significant modifications
        - Maintain code quality and consistency

        Remember: You can combine these tools to perform complex refactoring
        and development tasks. Always explain your approach before making changes.
        Important rules: If you are asked to make any edits to a file, always
        first view the file to understand its context and make sure you understand
        the impact of the changes. Only then make the changes.
        Ensure if specifiying line numbers, it's chosen with room (around 20
        lines before and 20 lines after the edit range)
        """,
            ),
            MessagesPlaceholder("chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder("agent_scratchpad"),
        ]
    )

    # Create the agent
    # agent = OpenAIFunctionsAgent(
    #     llm=llm,
    #     tools=tools,
    #     prompt=prompt,
    # )
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
    )

    # Create message history handler
    message_history = InMemoryChatMessageHistory(messages=chat_history)

    # Wrap with message history
    return RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: message_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )


def create_codebase_inspector_agent(
    codebase: Codebase,
    model_name: str = "gpt-4o",
    temperature: float = 0,
    verbose: bool = True,
    chat_history: list[BaseMessage] = [],
) -> RunnableWithMessageHistory:
    """Create an agent with all codebase tools.

    Args:
        codebase: The codebase to operate on
        model_name: Name of the model to use (default: gpt-4)
        temperature: Model temperature (default: 0)
        verbose: Whether to print agent's thought process (default: True)

    Returns:
        Initialized agent with message history
    """
    # Initialize language model
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
    )

    # Get all codebase tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
        DeleteFileTool(codebase),
        RevealSymbolTool(codebase),
    ]

    # Get the prompt to use
    prompt = pull("codegen-agent/codebase-agent")

    # Create the agent
    agent = OpenAIFunctionsAgent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
    )

    # Create message history handler
    message_history = InMemoryChatMessageHistory(messages=chat_history)

    # Wrap with message history
    return RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: message_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )


def create_agent_with_tools(
    codebase: Codebase,
    tools: list[BaseTool],
    model_name: str = "gpt-4o",
    temperature: float = 0,
    verbose: bool = True,
    chat_history: list[BaseMessage] = [],
) -> RunnableWithMessageHistory:
    """Create an agent with a specific set of tools.

    Args:
        codebase: The codebase to operate on
        tools: List of tools to provide to the agent
        model_name: Name of the model to use (default: gpt-4)
        temperature: Model temperature (default: 0)
        verbose: Whether to print agent's thought process (default: True)
        chat_history: Optional list of messages to initialize chat history with

    Returns:
        Initialized agent with message history
    """
    # Initialize language model
    llm = ChatOpenAI(
        model_name=model_name,
        temperature=temperature,
    )

    # Get the prompt to use
    prompt = pull("hwchase17/openai-functions-agent")

    # Create the agent
    agent = OpenAIFunctionsAgent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    # Create the agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=verbose,
    )

    # Create message history handler
    message_history = InMemoryChatMessageHistory(messages=chat_history)

    # Wrap with message history
    return RunnableWithMessageHistory(
        agent_executor,
        lambda session_id: message_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
