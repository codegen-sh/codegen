# Deep Code Research Example

This example demonstrates how to use Codegen to build a CLI tool for deep code research. The tool allows you to:

- Clone and analyze any GitHub repository
- Ask questions about the codebase
- Explore dependencies and relationships
- Search for patterns and implementations

## Setup

1. Install the requirements:

```bash
uv venv
source .venv/bin/activate
uv sync
```

2. Set up your OpenAI API key in a `.env`:

```bash
OPENAI_API_KEY=your-api-key
```

## Usage

Run the CLI tool by providing a GitHub repository:

```bash
python run.py research "owner/repo"
```

For example:

```bash
python run.py research "fastapi/fastapi"
```

You can also provide an initial query:

```bash
python run.py research "fastapi/fastapi" -q "Explain the main components"
```

## Example Queries

- "Explain the main components and their relationships"
- "Find all usages of the FastAPI class"
- "Show me the dependency graph for the routing module"
- "What design patterns are used in this codebase?"
- "How is dependency injection implemented?"

## Features

The research agent has access to several powerful tools:

- Semantic code search
- Symbol relationship analysis
- Directory structure exploration
- Code viewing and analysis

The agent maintains conversation history, so you can ask follow-up questions and build on previous findings.

## Exit

Type "exit" or "quit" to end the research session.
