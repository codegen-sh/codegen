# AgentGen

A library for building AI agents using LangChain and LangGraph.

## Installation

```bash
pip install -r requirements.txt
```

## Features

- Chat agents with memory
- Code analysis agents
- PR review agents
- Integration with GitHub, Linear, and Slack
- Extensible tool system

## Dependencies

This library uses the following packages:
- langchain (v0.3.22)
- langchain-core (v0.3.50)
- langchain-anthropic (v0.3.10)
- langchain-openai (v0.3.12)
- langgraph (v0.3.25)
- langgraph-prebuilt (v0.1.8)
- langchain-xai (v0.2.2)
- langsmith (v0.1.22)
- pydantic (v2+)

## Usage

```python
from agentgen.agents.chat_agent import ChatAgent
from codegen import Codebase

# Initialize a codebase
codebase = Codebase("path/to/repo")

# Create a chat agent
agent = ChatAgent(codebase, model_provider="anthropic", model_name="claude-3-5-sonnet-latest")

# Chat with the agent
response, thread_id = agent.chat("What files are in this repository?")
print(response)
```
