from typing import Annotated, Any

from mcp.server.fastmcp import Context, FastMCP

from codegen.cli.api.client import RestAPI
from codegen.cli.mcp.agent.docs_expert import create_sdk_expert_agent
from codegen.cli.mcp.resources.system_prompt import SYSTEM_PROMPT
from codegen.cli.mcp.resources.system_setup_instructions import SETUP_INSTRUCTIONS
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Initialize FastMCP server

mcp = FastMCP("codegen-mcp", instructions="MCP server for the Codegen SDK. Use the tools and resources to setup codegen in your environment and to create and improve your Codegen Codemods.")

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
def ask_codegen_sdk(query: Annotated[str, "Ask a question to an exper agent for details about any aspect of the codegen sdk core set of classes and utilities"]):
    codebase = Codebase("../../sdk/core")
    agent = create_sdk_expert_agent(codebase=codebase)

    result = agent.invoke(
        {"input": query},
        config={"configurable": {"thread_id": 1}},
    )

    return result["messages"][-1].content


@mcp.tool()
def generate_codemod(
    title: Annotated[str, "The title of the codemod (hyphenated)"],
    task: Annotated[str, "The task to which the codemod should implement to solve"],
    codebase_path: Annotated[str, "The absolute path to the codebase directory"],
    ctx: Context,
) -> str:
    """Generate a codemod for the given task and codebase."""
    return f'''
    Use the codegen cli to generate a codemod. If you need to intall the cli the command to do so is `uv tool install codegen`. Once installed, run the following command to generate the codemod:

    codegen create {title} -d "{task}"
    '''


@mcp.tool()
def improve_codemod(
    codemod_source: Annotated[str, "The source code of the codemod to improve"],
    task: Annotated[str, "The task to which the codemod should implement to solve"],
    concerns: Annotated[list[str], "A list of issues that were discovered with the current codemod that need to be considered in the next iteration"],
    context: Annotated[dict[str, Any], "Additional context for the codemod this can be a list of files that are related, additional information about the task, etc."],
    language: Annotated[ProgrammingLanguage, "The language of the codebase, i.e ALL CAPS PYTHON or TYPESCRIPT "],
    ctx: Context,
) -> str:
    """Improve the codemod."""
    try:
        client = RestAPI()
        response = client.improve_codemod(codemod_source, task, concerns, context, language)
        return response.codemod_source
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codegen server...")
    mcp.run(transport="stdio")
