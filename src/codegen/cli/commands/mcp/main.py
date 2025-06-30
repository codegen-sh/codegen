import os
import sys
from pathlib import Path
from typing import Optional
import typer
import rich
import subprocess

def mcp(
    port: Optional[int] = typer.Option(None, "--port", "-p", help="Port to run the MCP server on (for HTTP transport)"),
    transport: str = typer.Option("stdio", "--transport", "-t", help="Transport type: stdio, sse, or http"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Start the Codegen MCP server for integration with AI editors like Cursor."""
    
    # Get the path to the MCP server
    current_file = Path(__file__).resolve()
    mcp_server_path = current_file.parent.parent.parent / "mcp" / "server.py"
    
    if not mcp_server_path.exists():
        rich.print("[red]Error:[/red] MCP server not found. Please ensure Codegen is properly installed.")
        raise typer.Exit(1)
    
    # Prepare environment variables
    env = os.environ.copy()
    if verbose:
        env["CODEGEN_MCP_VERBOSE"] = "1"
    if port:
        env["CODEGEN_MCP_PORT"] = str(port)
    if transport:
        env["CODEGEN_MCP_TRANSPORT"] = transport
    
    try:
        rich.print(f"[green]Starting Codegen MCP server...[/green]")
        rich.print(f"[dim]Server path: {mcp_server_path}[/dim]")
        rich.print(f"[dim]Transport: {transport}[/dim]")
        if port:
            rich.print(f"[dim]Port: {port}[/dim]")
        
        # Run the MCP server
        result = subprocess.run([
            sys.executable, str(mcp_server_path)
        ], env=env, cwd=mcp_server_path.parent)
        
        if result.returncode != 0:
            rich.print(f"[red]Error:[/red] MCP server exited with code {result.returncode}")
            raise typer.Exit(result.returncode)
            
    except KeyboardInterrupt:
        rich.print("\n[yellow]MCP server stopped.[/yellow]")
        raise typer.Exit(0)
    except Exception as e:
        rich.print(f"[red]Error starting MCP server:[/red] {e}")
        raise typer.Exit(1)

