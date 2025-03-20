# Codegen LangChain Agent Example

<p align="center">
  <a href="https://docs.codegen.com/tutorials/build-code-agent">
    <img src="https://i.imgur.com/6RF9W0z.jpeg" />
  </a>
</p>

<h2 align="center">
  Build an intelligent code agent with LangChain and Codegen
</h2>

<div align="center">

[![Documentation](https://img.shields.io/badge/Docs-docs.codegen.com-purple?style=flat-square)](https://docs.codegen.com/tutorials/build-code-agent)
[![License](https://img.shields.io/badge/Code%20License-Apache%202.0-gray?&color=gray)](https://github.com/codegen-sh/codegen-sdk/tree/develop?tab=Apache-2.0-1-ov-file)

</div>

This example demonstrates how to build an intelligent code agent using Codegen's LangChain integration. The agent can analyze and manipulate codebases using natural language commands.

## Quick Start

```python
from codegen import Codebase
from codegen.extensions.langchain import create_codebase_agent

# Initialize codebase
codebase = Codebase.from_repo("fastapi/fastapi")

# Create the agent
agent = create_codebase_agent(
    codebase=codebase,
    model_provider="anthropic",  # or "openai"
    model_name="claude-3-5-sonnet-latest",  # or "gpt-4" for OpenAI
    debug=True,
)

# Ask the agent to analyze code
result = agent.invoke({"input": "What are the dependencies of the FastAPI class?", "config": {"configurable": {"thread_id": "1"}}})
print(result["messages"][-1].content)
```

## Installation

```bash
# Install dependencies
pip install modal-client codegen langchain langchain-openai

# Run the example
python run.py
```

## Available Tools

The agent comes with several built-in tools for code operations:

- `ViewFileTool`: View file contents and metadata
- `ListDirectoryTool`: List directory contents
- `RipGrepTool`: Search code using ripgrep
- `EditFileTool`: Edit file contents
- `CreateFileTool`: Create new files
- `DeleteFileTool`: Delete files
- `RenameFileTool`: Rename files and update imports
- `MoveSymbolTool`: Move functions/classes between files
- `RevealSymbolTool`: Analyze symbol dependencies
- `SemanticEditTool`: Make semantic code edits
- `CommitTool`: Commit changes to disk

## Example Operations

The agent can perform various code analysis and manipulation tasks:

```python
# Analyze dependencies
agent.invoke({"input": "What are the dependencies of the reveal_symbol function?", "config": {"configurable": {"thread_id": "1"}}})

# Find usage patterns
agent.invoke({"input": "Show me examples of dependency injection in the codebase", "config": {"configurable": {"thread_id": "1"}}})

# Move code
agent.invoke({"input": "Move the validate_email function to validation_utils.py", "config": {"configurable": {"thread_id": "1"}}})
```

## Learn More

- [Full Tutorial](https://docs.codegen.com/tutorials/build-code-agent)
