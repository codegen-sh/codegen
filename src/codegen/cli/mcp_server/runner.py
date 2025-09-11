"""MCP server runner for the Codegen platform."""

from fastmcp import FastMCP

from .resources import register_resources
from .tools.dynamic import register_dynamic_tools
from .tools.static import register_static_tools


def run_server(transport: str = "stdio", host: str = "localhost", port: int | None = None, available_tools: list | None = None):
    """Run the MCP server with the specified transport."""
    from .prompts import MCP_SERVER_INSTRUCTIONS

    # Initialize FastMCP server
    mcp = FastMCP(
        "codegen-mcp",
        instructions=MCP_SERVER_INSTRUCTIONS,
    )

    # Register all components
    register_resources(mcp)
    register_static_tools(mcp)

    # Register dynamic tools if provided
    if available_tools:
        print("🔧 Registering dynamic tools from API...")
        register_dynamic_tools(mcp, available_tools)
        print(f"✅ Registered {len(available_tools)} dynamic tools")

    if transport == "stdio":
        print("🚀 MCP server running on stdio transport")
        mcp.run(transport="stdio")
    elif transport == "http":
        if port is None:
            port = 8000
        print(f"🚀 MCP server running on http://{host}:{port}")
        # Note: FastMCP may not support HTTP transport directly
        # This is a placeholder for future HTTP transport support
        print(f"HTTP transport not yet implemented. Would run on {host}:{port}")
        mcp.run(transport="stdio")  # Fallback to stdio for now
    else:
        msg = f"Unsupported transport: {transport}"
        raise ValueError(msg)
