# Codegen MCP server

A MCP server implementation that provides tools and resources for using and working with the Codegen CLI and SDK, enabling AI agents to iterate quickly on writing codemods with the codegen sdk.

### Dependencies

- [fastmcp](https://github.com/codegen-sh/fastmcp)

## Usage

Most AI Agents that support MCP will have some way to configure the server startup.

### Cline

Add this to your `cline_mcp_settings.json` file to get started:

```
{
  "mcpServers": {
    "codegen-cli": {
        "command": "uv",
        "args": [
            "--directory",
            "<path to codegen installation>/codegen-sdk/src/codegen/cli/mcp",
            "run",
            "server.py"
        ]
    }
  }
}
```

Cursor:
Under the `Settings` > `Feature` > `MCP Servers` section, click "Add New MCP Server" and add the following:

```
Name: codegen-mcp
Type: Command
Command: uv --directory <path to codegen installation>/codegen-sdk/src/codegen/cli/mcp run server.py
```
