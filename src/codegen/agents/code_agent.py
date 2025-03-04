import os
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from langchain.tools import BaseTool
from langchain_core.messages import AIMessage
from langsmith import Client

from codegen.extensions.langchain.agent import create_codebase_agent
from codegen.extensions.langchain.utils.get_langsmith_url import find_and_print_langsmith_run_url

if TYPE_CHECKING:
    from codegen import Codebase


class CodeAgent:
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
        if tools is None:
            tools = []
        tools = [tool for tool in tools if tool.name not in ["reveal_symbol", "move_symbol"]]
        self.agent = create_codebase_agent(self.codebase, model_provider=model_provider, model_name=model_name, memory=memory, additional_tools=tools, **kwargs)
        self.langsmith_client = Client()

        self.project_name = os.environ.get("LANGCHAIN_PROJECT", "RELACE")
        print(f"Using LangSmith project: {self.project_name}")

    def run(self, prompt: str, thread_id: Optional[str] = None) -> str:
        """Run the agent with a prompt.

        Args:
            prompt: The prompt to run
            thread_id: Optional thread ID for message history

        Returns:
            The agent's response
        """
        if thread_id is None:
            thread_id = str(uuid4())

        input = {"messages": [("user", prompt)]}

        stream = self.agent.stream(input, config={"configurable": {"thread_id": thread_id, "metadata": {"project": self.project_name}}, "recursion_limit": 100}, stream_mode="values")

        run_ids = []

        for s in stream:
            message = s["messages"][-1]
            if isinstance(message, tuple):
                print(message)
            else:
                if isinstance(message, AIMessage) and isinstance(message.content, list) and "text" in message.content[0]:
                    AIMessage(message.content[0]["text"]).pretty_print()
                else:
                    message.pretty_print()

                if hasattr(message, "additional_kwargs") and "run_id" in message.additional_kwargs:
                    run_ids.append(message.additional_kwargs["run_id"])

        result = s["messages"][-1].content

        try:
            find_and_print_langsmith_run_url(self.langsmith_client, self.project_name)
        except Exception as e:
            separator = "=" * 60
            print(f"\n{separator}\nCould not retrieve LangSmith URL: {e}")
            import traceback

            print(traceback.format_exc())
            print(separator)

        return result

    def get_agent_trace_url(self) -> str | None:
        """Get the URL for the most recent agent run in LangSmith.

        Returns:
            The URL for the run in LangSmith if found, None otherwise
        """
        try:
            return find_and_print_langsmith_run_url(client=self.langsmith_client, project_name=self.project_name)
        except Exception as e:
            separator = "=" * 60
            print(f"\n{separator}\nCould not retrieve LangSmith URL: {e}")
            import traceback

            print(traceback.format_exc())
            print(separator)
            return None
