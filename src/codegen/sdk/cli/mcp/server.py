from typing import Annotated, Any

from mcp.server.fastmcp import Context, FastMCP

from codegen.sdk.cli.mcp.resources.system_prompt import SYSTEM_PROMPT
from codegen.sdk.cli.mcp.resources.system_setup_instructions import SETUP_INSTRUCTIONS

# Initialize FastMCP server

mcp = FastMCP("codegen-mcp", instructions="MCP server for the Codegen SDK. Use the tools and resources to setup codegen in your environment and to create and improve your Graph-sitter Codemods.")

# ----- RESOURCES -----


@mcp.resource("system://agent_prompt", description="Provides all the information the agent needs to know about Codegen SDK", mime_type="text/plain")
def get_docs() -> str:
    """Get the sdk doc url."""
    return SYSTEM_PROMPT


@mcp.resource("system://setup_instructions", description="Provides all the instructions to setup the environment for the agent", mime_type="text/plain")
def get_setup_instructions() -> str:
    """Get the setup instructions."""
    return SETUP_INSTRUCTIONS


@mcp.resource("system://manifest", mime_type="application/json")
def get_service_config() -> dict[str, Any]:
    """Get the service config."""
    return {
        "name": "mcp-codegen",
        "version": "0.1.0",
        "description": "The MCP server for assisting with creating/writing/improving codegen codemods.",
    }


# ----- TOOLS -----


@mcp.tool()
def generate_codemod(
    title: Annotated[str, "The title of the codemod (hyphenated)"],
    codebase_path: Annotated[str, "The absolute path to the codebase directory"],
    ctx: Context,
) -> str:
    """Generate a codemod for the given task and codebase."""
    return f"""
    Use the codegen.sdk.cli to generate a codemod. If you need to intall the cli the command to do so is `uv tool install graph-sitter`.
    Once installed, run the following command to generate the codemod:

    gs create {title}"
    """


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codegen server...")
    mcp.run(transport="stdio")
