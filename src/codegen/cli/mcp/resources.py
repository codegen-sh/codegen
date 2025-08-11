"""MCP resources for the Codegen server."""

from typing import Any

from fastmcp import FastMCP


def register_resources(mcp: FastMCP):
    """Register MCP resources with the server."""

    @mcp.resource("system://manifest", mime_type="application/json")
    def get_service_config() -> dict[str, Any]:
        """Get the service config."""
        return {
            "name": "mcp-codegen",
            "version": "0.1.0",
            "description": "The MCP server for the Codegen platform API integration.",
        }
