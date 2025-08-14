"""Main MCP server entry point for the Codegen platform.

This module provides the main entry point for the Codegen MCP server.
The actual server functionality is distributed across several modules:

- api_client.py: API client management
- prompts.py: Server instructions and prompts
- resources.py: MCP resources
- tools/: Tool modules (static and dynamic)
- runner.py: Server runner and configuration
"""

from .runner import run_server

if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codegen server...")
    run_server()
