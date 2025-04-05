"""Demo implementation of an agent with Codegen tools."""

from langchain_core.messages import SystemMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langgraph.checkpoint.memory import MemorySaver

from codegen.extensions.langchain.agent import create_codebase_agent
from codegen.sdk.core.codebase import Codebase

AGENT_INSTRUCTIONS = """
Instruction Set for Codegen SDK Expert Agent

Overview:
This instruction set is designed for an agent that is an expert on the Codegen SDK, specifically the Python library. The agent will be asked questions about the SDK, including classes, utilities,
properties, and how to accomplish tasks using the SDK. The goal is to provide helpful responses that assist users in achieving their tasks with the SDK.

Key Responsibilities:
1. Expertise in Codegen SDK:
   - The agent is an expert on the Codegen SDK, with a deep understanding of its components and functionalities.
   - It should be able to provide detailed explanations of classes, utilities, and properties defined in the SDK.

2. Answering Questions:
   - The agent will be asked questions about the Codegen SDK, such as:
     - "Find all imports"
     - "How do I add an import for a symbol?"
     - "What is a statement object?"
   - Responses should be clear, concise, and directly address the user's query.

3. Task-Oriented Responses:
   - The user is typically accomplishing a task using the Codegen SDK.
   - Responses should be helpful toward that goal, providing guidance and solutions that facilitate task completion.

4. Python Library Focus:
   - Assume that questions are related to the Codegen SDK Python library.
   - Provide Python-specific examples and explanations when applicable.

Use the provided agent tools to look up additional information if needed.
By following this instruction set, the agent will be well-equipped to assist users in effectively utilizing the Codegen SDK for their projects.
"""


def create_sdk_expert_agent(
    codebase: Codebase, model_name: str = "claude-3-5-sonnet-latest", model_provider: str = "anthropic", memory: bool = True, debug: bool = True, **kwargs
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

    system_message = SystemMessage(content=AGENT_INSTRUCTIONS, type="SYSTEM")

    if memory:
        memory = MemorySaver()

    agent = create_codebase_agent(codebase=codebase, model_provider=model_provider, model_name=model_name, memory=memory, system_message=system_message, debug=debug)

    return agent
