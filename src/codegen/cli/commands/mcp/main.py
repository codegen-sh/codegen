import logging
import sys
from pathlib import Path
from typing import Optional

import rich
import rich_click as click
from mcp.server.fastmcp import Context, FastMCP
from rich.logging import RichHandler
from rich.panel import Panel

from codegen.cli.api.client import RestAPI
from codegen.cli.mcp.agent.docs_expert import create_sdk_expert_agent
from codegen.cli.mcp.resources.system_prompt import SYSTEM_PROMPT
from codegen.cli.mcp.resources.system_setup_instructions import SETUP_INSTRUCTIONS
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage


def setup_logging(debug: bool = False):
    """Configure rich logging with colors."""
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(message)s",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                tracebacks_show_locals=debug,
                markup=True,
                show_time=False,
            )
        ],
    )


def create_mcp_server(repo_path: Optional[Path] = None) -> FastMCP:
    """Create and configure the MCP server with the given repository."""
    # Initialize FastMCP server
    mcp = FastMCP(
        "codegen-mcp",
        instructions="MCP server for the Codegen SDK. Use the tools and resources to setup codegen in your environment and to create and improve your Codegen Codemods.",
    )

    # ----- RESOURCES -----
    @mcp.resource(
        "system://agent_prompt",
        description="Provides all the information the agent needs to know about Codegen SDK",
        mime_type="text/plain",
    )
    def get_docs() -> str:
        """Get the sdk doc url."""
        return SYSTEM_PROMPT

    @mcp.resource(
        "system://setup_instructions",
        description="Provides all the instructions to setup the environment for the agent",
        mime_type="text/plain",
    )
    def get_setup_instructions() -> str:
        """Get the setup instructions."""
        return SETUP_INSTRUCTIONS

    @mcp.resource("system://manifest", mime_type="application/json")
    def get_service_config() -> dict:
        """Get the service config."""
        return {
            "name": "mcp-codegen",
            "version": "0.1.0",
            "description": "The MCP server for assisting with creating/writing/improving codegen codemods.",
        }

    # ----- TOOLS -----
    @mcp.tool()
    def ask_codegen_sdk(query: str):
        """Ask a question to an expert agent for details about any aspect of the codegen sdk."""
        codebase_path = repo_path or "../../sdk/core"
        codebase = Codebase(codebase_path)
        agent = create_sdk_expert_agent(codebase=codebase)

        result = agent.invoke(
            {"input": query},
            config={"configurable": {"thread_id": 1}},
        )

        return result["messages"][-1].content

    @mcp.tool()
    def generate_codemod(
        title: str,
        task: str,
        codebase_path: str,
        ctx: Context,
    ) -> str:
        """Generate a codemod for the given task and codebase."""
        return f'''
        Use the codegen cli to generate a codemod. If you need to intall the cli the command to do so is `uv tool install codegen`. Once installed, run the following command to generate the codemod:

        codegen create {title} -d "{task}"
        '''

    @mcp.tool()
    def improve_codemod(
        codemod_source: str,
        task: str,
        concerns: list[str],
        context: dict,
        language: ProgrammingLanguage,
        ctx: Context,
    ) -> str:
        """Improve the codemod."""
        try:
            client = RestAPI()
            response = client.improve_codemod(codemod_source, task, concerns, context, language)
            return response.codemod_source
        except Exception as e:
            return f"Error: {e}"

    return mcp


@click.command(name="mcp")
@click.option(
    "--repo",
    "-r",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help="Path to the repository to analyze",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode with detailed logging",
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="Transport method for the MCP server",
)
def mcp_command(repo: Optional[Path], debug: bool, transport: str):
    """Run the Codegen MCP server for AI-assisted codemod development.

    The MCP (Mission Control Protocol) server provides an interface for AI agents
    to help you create, improve, and understand Codegen codemods.
    """
    # Configure logging
    setup_logging(debug)

    # Print server info
    rich.print(
        Panel(
            f"[green]Starting Codegen MCP Server[/green]\n[dim]Repository:[/dim] {repo or 'Not specified'}\n[dim]Transport:[/dim] {transport}\n[dim]Debug:[/dim] {'enabled' if debug else 'disabled'}",
            title="[bold]MCP Server Info[/bold]",
            border_style="blue",
        )
    )

    try:
        # Create and run the MCP server
        mcp = create_mcp_server(repo)

        if transport == "http":
            mcp.run(transport=transport)
        else:
            mcp.run(transport=transport)

    except Exception as e:
        logging.exception(f"Error running MCP server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    mcp_command()
