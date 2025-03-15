from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from langchain.tools import BaseTool
from langchain_core.messages import AIMessage

from codegen.extensions.langchain.agent import create_chat_agent

if TYPE_CHECKING:
    from codegen import Codebase


class ChatAgent:
    """Agent for interacting with a codebase."""

    def __init__(self, codebase: "Codebase", model_provider: str = "anthropic", model_name: str = "claude-3-5-sonnet-latest", memory: bool = True, tools: Optional[list[BaseTool]] = None, **kwargs):
        """Initialize a CodeAgent.

        Args:
            codebase: The codebase to operate on
            model_provider: The model provider to use ("anthropic" or "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            tools: Additional tools to use
            **kwargs: Additional LLM configuration options. Supported options:
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
                - max_tokens: Maximum number of tokens to generate
        """
        self.codebase = codebase
        self.agent = create_chat_agent(self.codebase, model_provider=model_provider, model_name=model_name, memory=memory, additional_tools=tools, **kwargs)

    def run(self, prompt: str, thread_id: Optional[str] = None) -> str:
        """Run the agent with a prompt.

        Args:
            prompt: The prompt to run
            thread_id: Optional thread ID for message history. If None, a new thread is created.

        Returns:
            The agent's response
        """
        if thread_id is None:
            thread_id = str(uuid4())

        input = {"query": prompt}
        stream = self.agent.stream(input, config={"configurable": {"thread_id": thread_id}}, stream_mode="values")

        for s in stream:
            message = s["messages"][-1]
            if isinstance(message, tuple):
                print(message)
            else:
                if isinstance(message, AIMessage) and isinstance(message.content, list) and "text" in message.content[0]:
                    AIMessage(message.content[0]["text"]).pretty_print()
                else:
                    message.pretty_print()

        return s["final_answer"]

    def chat(self, prompt: str, thread_id: Optional[str] = None) -> tuple[str, str]:
        """Chat with the agent, maintaining conversation history.

        Args:
            prompt: The user message
            thread_id: Optional thread ID for message history. If None, a new thread is created.

        Returns:
            A tuple of (response_content, thread_id) to allow continued conversation
        """
        if thread_id is None:
            thread_id = str(uuid4())
            print(f"Starting new chat thread: {thread_id}")
        else:
            print(f"Continuing chat thread: {thread_id}")

        response = self.run(prompt, thread_id=thread_id)
        return response, thread_id

    def get_chat_history(self, thread_id: str) -> list:
        """Retrieve the chat history for a specific thread.

        Args:
            thread_id: The thread ID to retrieve history for

        Returns:
            List of messages in the conversation history
        """
        # Access the agent's memory to get conversation history
        if hasattr(self.agent, "get_state"):
            state = self.agent.get_state({"configurable": {"thread_id": thread_id}})
            if state and "messages" in state:
                return state["messages"]
        return []
