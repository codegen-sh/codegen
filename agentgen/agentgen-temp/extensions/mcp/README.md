# Codegen MCP Servers

This directory contains reference implementations of MCP (Machine Control Protocol) servers that extend AI Agent capabilities using the Codegen SDK. These servers enable AI Agents to:

- Query and analyze your codebase (`codebase_agent.py`)
- Run deterministic codemods (`codebase_mods.py`)
- Invoke tools built with Codegen SDK (`codebase_tools.py`)

## What is MCP?

MCP (Model Context Protocol) allows AI Agents to interact with local tools and services through a standardized interface. The servers in this directory demonstrate how you might write an MCP server that leverages Codegen's capabilities.

## Setup Instructions

### Cline

Add this to your `cline_mcp_settings.json` file to get started:

```
{
  "mcpServers": {
    "codegen-cli": {
        "command": "uv",
        "args": [
            "--directory",
            "<path to codegen installation>/codegen-sdk/src/codegen/extensions/mcp",
            "run",
            "codebase_agent.py | codebase_mods | codebase_tools"
        ]
    }
  }
}
```

### Cursor:

Under the `Settings` > `Feature` > `MCP Servers` section, click "Add New MCP Server" and add the following:

```
Name: codegen-mcp
Type: Command
Command: uv --directory <path to codegen installation>/codegen-sdk/src/codegen/cli/mcp run <codebase_agent.py | codebase_mods | codebase_tools>
```
