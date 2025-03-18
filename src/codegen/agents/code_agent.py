import os
from typing import TYPE_CHECKING, Optional
from uuid import uuid4

from langchain.tools import BaseTool
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.graph.graph import CompiledGraph
from langsmith import Client

from codegen.agents.loggers import ExternalLogger
from codegen.agents.tracer import MessageStreamTracer
from codegen.extensions.langchain.agent import create_codebase_agent
from codegen.extensions.langchain.utils.get_langsmith_url import (
    find_and_print_langsmith_run_url,
)

if TYPE_CHECKING:
    from codegen import Codebase

from codegen.agents.utils import AgentConfig


class CodeAgent:
    """Agent for interacting with a codebase."""

    codebase: "Codebase"
    agent: CompiledGraph
    langsmith_client: Client
    project_name: str
    thread_id: str | None = None
    run_id: str | None = None
    instance_id: str | None = None
    difficulty: int | None = None
    logger: Optional[ExternalLogger] = None

    def __init__(
        self,
        codebase: "Codebase",
        model_provider: str = "anthropic",
        model_name: str = "claude-3-7-sonnet-latest",
        memory: bool = True,
        tools: Optional[list[BaseTool]] = None,
        tags: Optional[list[str]] = [],
        metadata: Optional[dict] = {},
        agent_config: Optional[AgentConfig] = None,
        thread_id: Optional[str] = None,
        logger: Optional[ExternalLogger] = None,
        **kwargs,
    ):
        """Initialize a CodeAgent.

        Args:
            codebase: The codebase to operate on
            model_provider: The model provider to use ("anthropic" or "openai")
            model_name: Name of the model to use
            memory: Whether to let LLM keep track of the conversation history
            tools: Additional tools to use
            tags: Tags to add to the agent trace. Must be of the same type.
            metadata: Metadata to use for the agent. Must be a dictionary.
            **kwargs: Additional LLM configuration options. Supported options:
                - temperature: Temperature parameter (0-1)
                - top_p: Top-p sampling parameter (0-1)
                - top_k: Top-k sampling parameter (>= 1)
                - max_tokens: Maximum number of tokens to generate
        """
        self.codebase = codebase
        self.agent = create_codebase_agent(
            self.codebase,
            model_provider=model_provider,
            model_name=model_name,
            memory=memory,
            additional_tools=tools,
            config=agent_config,
            **kwargs,
        )
        self.model_name = model_name
        self.langsmith_client = Client()

        if thread_id is None:
            self.thread_id = str(uuid4())
        else:
            self.thread_id = thread_id

        # Get project name from environment variable or use a default
        self.project_name = os.environ.get("LANGCHAIN_PROJECT", "RELACE")
        print(f"Using LangSmith project: {self.project_name}")

        # Store SWEBench metadata if provided
        self.run_id = metadata.get("run_id")
        self.instance_id = metadata.get("instance_id")
        # Extract difficulty value from "difficulty_X" format
        difficulty_str = metadata.get("difficulty", "")
        self.difficulty = int(difficulty_str.split("_")[1]) if difficulty_str and "_" in difficulty_str else None

        # Initialize tags for agent trace
        self.tags = [*tags, self.model_name]

        # set logger if provided
        self.logger = logger

        # Initialize metadata for agent trace
        self.metadata = {
            "project": self.project_name,
            "model": self.model_name,
            **metadata,
        }

    def run(self, prompt: str) -> str:
        """Run the agent with a prompt.

        Args:
            prompt: The prompt to run
            thread_id: Optional thread ID for message history

        Returns:
            The agent's response
        """
        self.config = {
            "configurable": {
                "thread_id": self.thread_id,
                "metadata": {"project": self.project_name},
            },
            "recursion_limit": 100,
        }

        # this message has a reducer which appends the current message to the existing history
        # see more https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
        input = {"query": prompt}

        config = RunnableConfig(configurable={"thread_id": self.thread_id}, tags=self.tags, metadata=self.metadata, recursion_limit=200)
        # we stream the steps instead of invoke because it allows us to access intermediate nodes

        stream = self.agent.stream(input, config=config, stream_mode="values")

        _tracer = MessageStreamTracer(logger=self.logger)

        # Process the stream with the tracer
        traced_stream = _tracer.process_stream(stream)

        # Keep track of run IDs from the stream
        run_ids = []

        for s in traced_stream:
            if len(s["messages"]) == 0 or isinstance(s["messages"][-1], HumanMessage):
                message = HumanMessage(content=prompt)
            else:
                message = s["messages"][-1]

            if isinstance(message, tuple):
                # print(message)
                pass
            else:
                if isinstance(message, AIMessage) and isinstance(message.content, list) and len(message.content) > 0 and "text" in message.content[0]:
                    AIMessage(message.content[0]["text"]).pretty_print()
                else:
                    message.pretty_print()

                # Try to extract run ID if available in metadata
                if hasattr(message, "additional_kwargs") and "run_id" in message.additional_kwargs:
                    run_ids.append(message.additional_kwargs["run_id"])

        # Get the last message content
        result = s["final_answer"]

        # # Try to find run IDs in the LangSmith client's recent runs
        try:
            # Find and print the LangSmith run URL
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
            # TODO - this is definitely not correct, we should be able to get the URL directly...
            return find_and_print_langsmith_run_url(client=self.langsmith_client, project_name=self.project_name)
        except Exception as e:
            separator = "=" * 60
            print(f"\n{separator}\nCould not retrieve LangSmith URL: {e}")
            import traceback

            print(traceback.format_exc())
            print(separator)
            return None

    def get_tools(self) -> list[BaseTool]:
        return list(self.agent.get_graph().nodes["tools"].data.tools_by_name.values())

    def get_state(self) -> dict:
        return self.agent.get_state(self.config)

    def get_tags_metadata(self) -> tuple[list[str], dict]:
        tags = [self.model_name]
        metadata = {"project": self.project_name, "model": self.model_name}
        # Add SWEBench run ID and instance ID to the metadata and tags for filtering
        if self.run_id is not None:
            metadata["swebench_run_id"] = self.run_id
            tags.append(self.run_id)

        if self.instance_id is not None:
            metadata["swebench_instance_id"] = self.instance_id
            tags.append(self.instance_id)

        if self.difficulty is not None:
            metadata["swebench_difficulty"] = self.difficulty
            tags.append(f"difficulty_{self.difficulty}")

        return tags, metadata
