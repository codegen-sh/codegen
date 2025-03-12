"""Demo implementation of an agent with Codegen tools."""

from codegen import Codebase
from codegen.extensions.langchain.tools import (
    CommitTool,
    CreateFileTool,
    DeleteFileTool,
    EditFileTool,
    ListDirectoryTool,
    MoveSymbolTool,
    RenameFileTool,
    RevealSymbolTool,
    SearchTool,
    SemanticEditTool,
    ViewFileTool,
)

from codegen.extensions.langchain.llm import LLM
from codegen.extensions.langchain.prompts import REASONER_SYSTEM_MESSAGE

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.graph import CompiledGraph
from codegen.extensions.langchain.graph import create_react_agent
from langchain_core.messages import SystemMessage


def create_codebase_agent(
    codebase: "Codebase",
    model_provider: str = "anthropic",
    model_name: str = "claude-3-5-sonnet-latest",
    system_message: SystemMessage = SystemMessage(REASONER_SYSTEM_MESSAGE),
    memory: bool = True,
    debug: bool = True,
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

    # Get all codebase tools
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
        CommitTool(codebase),
    ]

    memory = MemorySaver() if memory else None

    return create_react_agent(model=llm, tools=tools, system_message=system_message, checkpointer=memory, debug=debug)


if __name__ == "__main__":
    # Initialize codebase
    print("Initializing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi", language="python")

    # Create agent with history
    print("Creating agent...")
    agent = create_codebase_agent(codebase)

    print("\nAsking agent to analyze symbol relationships...")
    result = agent.invoke(
        {"input": "What are the dependencies of the reveal_symbol function?"},
        config={"configurable": {"thread_id": 1}},
    )
    print("Messages:", result["messages"])
