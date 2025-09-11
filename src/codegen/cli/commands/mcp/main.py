"""MCP command implementation."""

import typer
from codegen.cli.mcp_server.runner import run_server


def mcp(
    transport: str = typer.Option("stdio", help="Transport type (stdio, http)"),
    host: str = typer.Option("localhost", help="Host to bind to (for http transport)"),
    port: int = typer.Option(8000, help="Port to bind to (for http transport)"),
):
    """Start the Codegen MCP server."""
    run_server(transport=transport, host=host, port=port)
