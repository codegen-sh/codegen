# Codegen MCP Server

<p align="center">
  <a href="https://docs.codegen.com">
    <img src="https://i.imgur.com/6RF9W0z.jpeg" />
  </a>
</p>

<h2 align="center">
  An MCP server implementation that integrates the codegen sdk.

</h2>

<div align="center">

[![Documentation](https://img.shields.io/badge/Docs-docs.codegen.com-purple?style=flat-square)](https://docs.codegen.com)
[![License](https://img.shields.io/badge/Code%20License-Apache%202.0-gray?&color=gray)](https://github.com/codegen-sh/codegen-sdk/tree/develop?tab=Apache-2.0-1-ov-file)

</div>

This example demonstrates how to run a Model Control Protocol (MCP) server that integrates with Codegen. The server provides:

1. A standardized interface for model inference
1. Integration with Codegen's core functionality, parsing codebases and executing codemods
1. Support for various LLM providers through the MCP protocol

## Quick Start

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [python](https://www.python.org/downloads/) 3.12+

### Direct Execution

1. No installation is necessary, with the following command. Run this command directly or add it your `.json` mcp config file.

```bash
 uvx --from 'git+https://github.com/codegen-sh/codegen-sdk.git#egg=codegen-mcp-server&subdirectory=codegen-examples/examples/codegen-mcp-server' codegen-mcp-server
```

### Example MCP Config

Here is an example mcp config that can be used with Cline or Claude desktop to integrate this MCP server

```json
{
  "mcpServers": {
    "codegen-mcp": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/codegen-sh/codegen-sdk.git#egg=codegen-mcp-server&subdirectory=codegen-examples/examples/codegen-mcp-server",
        "codegen-mcp-server"
      ],
      "disabled": false,
      "autoApprove": []
    }
  }
}
```

###MCP Tools:

- `parse_codebase`: Parses a codebase located at the provided path.
- `check_parse_status`: Provides the current parsing status for the provided codebase.
- `execute_codemod`: Executes a codemod script on a parsed codebase. This is where the codegen sdk leveraged to run simple or sophisticated codemods on the codebase.
