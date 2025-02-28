import os
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from langchain.tools import BaseTool
from langchain_core.messages import AIMessage
from langsmith import Client

from codegen.extensions.langchain.agent import create_codebase_agent

if TYPE_CHECKING:
    from codegen import Codebase

# Remove logger configuration
# logger = logging.getLogger(__name__)


class CodeAgent:
    """Agent for interacting with a codebase."""

    def __init__(self, codebase: "Codebase", model_provider: str = "anthropic", model_name: str = "claude-3-7-sonnet-latest", memory: bool = True, tools: Optional[list[BaseTool]] = None, **kwargs):
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
        self.agent = create_codebase_agent(self.codebase, model_provider=model_provider, model_name=model_name, memory=memory, additional_tools=tools, **kwargs)
        self.langsmith_client = Client()

        # Get project name from environment variable or use a default
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

        # this message has a reducer which appends the current message to the existing history
        # see more https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
        input = {"messages": [("user", prompt)]}

        # we stream the steps instead of invoke because it allows us to access intermediate nodes
        stream = self.agent.stream(input, config={"configurable": {"thread_id": thread_id, "metadata": {"project": self.project_name}}, "recursion_limit": 100}, stream_mode="values")

        # Keep track of run IDs from the stream
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

                # Try to extract run ID if available in metadata
                if hasattr(message, "additional_kwargs") and "run_id" in message.additional_kwargs:
                    run_ids.append(message.additional_kwargs["run_id"])

        # Get the last message content
        result = s["messages"][-1].content

        # Try to find run IDs in the LangSmith client's recent runs
        try:
            # Get the most recent runs with proper filter parameters
            # We need to provide at least one filter parameter as required by the API
            recent_runs = list(
                self.langsmith_client.list_runs(
                    # Use the project name from environment variable
                    project_name=self.project_name,
                    # Limit to just the most recent run
                    limit=1,
                )
            )

            if recent_runs and len(recent_runs) > 0:
                # Make sure we have a valid run object with an id attribute
                if hasattr(recent_runs[0], "id"):
                    # Convert the ID to string to ensure it's in the right format
                    run_id = str(recent_runs[0].id)

                    # Get the run URL using the run_id parameter
                    run_url = self.get_langsmith_url(run_id=run_id)

                    separator = "=" * 60
                    print(f"\n{separator}\n🔍 LangSmith Run URL: {run_url}\n{separator}")
                else:
                    separator = "=" * 60
                    print(f"\n{separator}\nRun object has no 'id' attribute: {recent_runs[0]}\n{separator}")
            else:
                # If no runs found with project name, try a more general approach
                # Use a timestamp filter to get recent runs (last 10 minutes)
                import datetime

                ten_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=10)

                recent_runs = list(self.langsmith_client.list_runs(start_time=ten_minutes_ago.isoformat(), limit=1))

                if recent_runs and len(recent_runs) > 0 and hasattr(recent_runs[0], "id"):
                    # Convert the ID to string to ensure it's in the right format
                    run_id = str(recent_runs[0].id)

                    # Get the run URL using the run_id parameter
                    run_url = self.get_langsmith_url(run_id=run_id)

                    separator = "=" * 60
                    print(f"\n{separator}\n🔍 LangSmith Run URL: {run_url}\n{separator}")
                else:
                    separator = "=" * 60
                    print(f"\n{separator}\nNo valid runs found\n{separator}")
        except Exception as e:
            separator = "=" * 60
            print(f"\n{separator}\nCould not retrieve LangSmith URL: {e}")
            import traceback

            print(traceback.format_exc())
            print(separator)

        return result

    def get_langsmith_url(self, run_id: str, project_name: Optional[str] = None) -> str:
        """Get the URL for a run in LangSmith.

        Args:
            run_id: The ID of the run
            project_name: Optional name of the project

        Returns:
            The URL for the run in LangSmith
        """
        # Construct the URL directly using the host URL and run ID
        # This avoids the issue with the client's get_run_url method expecting a run object
        host_url = self.langsmith_client._host_url
        tenant_id = self.langsmith_client._get_tenant_id()

        # If project_name is not provided, use the default one
        if project_name is None:
            project_name = self.project_name

        try:
            # Get the project ID from the project name
            project_id = self.langsmith_client.read_project(project_name=project_name).id
            # Construct the URL
            return f"{host_url}/o/{tenant_id}/projects/p/{project_id}/r/{run_id}?poll=true"
        except Exception as e:
            # If we can't get the project ID, construct a URL without it
            print(f"Could not get project ID for {project_name}: {e}")
            return f"{host_url}/o/{tenant_id}/r/{run_id}?poll=true"
