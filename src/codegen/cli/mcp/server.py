import json
import os
from typing import Annotated, Any

from fastmcp import Context, FastMCP

from codegen.cli.mcp.resources.system_prompt import SYSTEM_PROMPT
from codegen.cli.mcp.resources.system_setup_instructions import SETUP_INSTRUCTIONS

# Optional imports for existing functionality
try:
    from codegen.cli.api.client import RestAPI
    from codegen.shared.enums.programming_language import ProgrammingLanguage

    LEGACY_IMPORTS_AVAILABLE = True
except ImportError:
    LEGACY_IMPORTS_AVAILABLE = False

# Import API client components
try:
    from codegen_api_client import ApiClient, Configuration
    from codegen_api_client.api import AgentsApi, OrganizationsApi, UsersApi
    from codegen_api_client.models import CreateAgentRunInput

    API_CLIENT_AVAILABLE = True
except ImportError:
    API_CLIENT_AVAILABLE = False

# Initialize FastMCP server
mcp = FastMCP(
    "codegen-mcp",
    instructions="MCP server for the Codegen platform. Use the tools and resources to interact with Codegen APIs, setup codegen in your environment, and create/improve Codegen Codemods.",
)

# Global API client instances
_api_client = None
_agents_api = None
_organizations_api = None
_users_api = None


def get_api_client():
    """Get or create the API client instance."""
    global _api_client, _agents_api, _organizations_api, _users_api

    if not API_CLIENT_AVAILABLE:
        msg = "codegen-api-client is not available"
        raise RuntimeError(msg)

    if _api_client is None:
        # Configure the API client
        configuration = Configuration()

        # Set base URL from environment or use default
        base_url = os.getenv("CODEGEN_API_BASE_URL", "https://api.codegen.com")
        configuration.host = base_url

        # Set authentication
        api_key = os.getenv("CODEGEN_API_KEY")
        if api_key:
            configuration.api_key = {"Authorization": f"Bearer {api_key}"}

        _api_client = ApiClient(configuration)
        _agents_api = AgentsApi(_api_client)
        _organizations_api = OrganizationsApi(_api_client)
        _users_api = UsersApi(_api_client)

    return _api_client, _agents_api, _organizations_api, _users_api


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


# Legacy SDK tool (only available if imports are available)
if LEGACY_IMPORTS_AVAILABLE:

    @mcp.tool()
    def ask_codegen_sdk(query: Annotated[str, "Ask a question to an expert agent for details about any aspect of the codegen sdk core set of classes and utilities"]):
        """Ask questions about the Codegen SDK (requires legacy imports)."""
        return "This tool requires additional dependencies that are not currently available."


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


# Legacy improve codemod tool (only available if imports are available)
if LEGACY_IMPORTS_AVAILABLE:

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


# ----- CODEGEN API TOOLS -----


@mcp.tool()
def create_agent_run(
    org_id: Annotated[int, "Organization ID"],
    prompt: Annotated[str, "The prompt/task for the agent to execute"],
    repo_name: Annotated[str | None, "Repository name (optional)"] = None,
    branch_name: Annotated[str | None, "Branch name (optional)"] = None,
    ctx: Context = None,
) -> str:
    """Create a new agent run in the specified organization."""
    try:
        _, agents_api, _, _ = get_api_client()

        # Create the input object
        agent_input = CreateAgentRunInput(prompt=prompt, repo_name=repo_name, branch_name=branch_name)

        # Make the API call
        response = agents_api.create_agent_run_v1_organizations_org_id_agent_run_post(org_id=org_id, create_agent_run_input=agent_input)

        return json.dumps(
            {
                "id": response.id,
                "status": response.status,
                "created_at": response.created_at.isoformat() if response.created_at else None,
                "prompt": response.prompt,
                "repo_name": response.repo_name,
                "branch_name": response.branch_name,
            },
            indent=2,
        )

    except Exception as e:
        return f"Error creating agent run: {e}"


@mcp.tool()
def get_agent_run(
    org_id: Annotated[int, "Organization ID"],
    agent_run_id: Annotated[int, "Agent run ID"],
    ctx: Context = None,
) -> str:
    """Get details of a specific agent run."""
    try:
        _, agents_api, _, _ = get_api_client()

        response = agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get(org_id=org_id, agent_run_id=agent_run_id)

        return json.dumps(
            {
                "id": response.id,
                "status": response.status,
                "created_at": response.created_at.isoformat() if response.created_at else None,
                "updated_at": response.updated_at.isoformat() if response.updated_at else None,
                "prompt": response.prompt,
                "repo_name": response.repo_name,
                "branch_name": response.branch_name,
                "result": response.result,
            },
            indent=2,
        )

    except Exception as e:
        return f"Error getting agent run: {e}"


@mcp.tool()
def get_organizations(
    page: Annotated[int, "Page number (default: 1)"] = 1,
    limit: Annotated[int, "Number of organizations per page (default: 10)"] = 10,
    ctx: Context = None,
) -> str:
    """Get list of organizations the user has access to."""
    try:
        _, _, organizations_api, _ = get_api_client()

        response = organizations_api.get_organizations_v1_organizations_get()

        # Format the response
        organizations = []
        for org in response.items:
            organizations.append({"id": org.id, "name": org.name, "slug": org.slug, "created_at": org.created_at.isoformat() if org.created_at else None})

        return json.dumps({"organizations": organizations, "total": response.total, "page": response.page, "limit": response.limit}, indent=2)

    except Exception as e:
        return f"Error getting organizations: {e}"


@mcp.tool()
def get_users(
    org_id: Annotated[int, "Organization ID"],
    page: Annotated[int, "Page number (default: 1)"] = 1,
    limit: Annotated[int, "Number of users per page (default: 10)"] = 10,
    ctx: Context = None,
) -> str:
    """Get list of users in an organization."""
    try:
        _, _, _, users_api = get_api_client()

        response = users_api.get_users_v1_organizations_org_id_users_get(org_id=org_id)

        # Format the response
        users = []
        for user in response.items:
            users.append({"id": user.id, "email": user.email, "name": user.name, "created_at": user.created_at.isoformat() if user.created_at else None})

        return json.dumps({"users": users, "total": response.total, "page": response.page, "limit": response.limit}, indent=2)

    except Exception as e:
        return f"Error getting users: {e}"


@mcp.tool()
def get_user(
    org_id: Annotated[int, "Organization ID"],
    user_id: Annotated[int, "User ID"],
    ctx: Context = None,
) -> str:
    """Get details of a specific user in an organization."""
    try:
        _, _, _, users_api = get_api_client()

        response = users_api.get_user_v1_organizations_org_id_users_user_id_get(org_id=org_id, user_id=user_id)

        return json.dumps(
            {
                "id": response.id,
                "email": response.email,
                "name": response.name,
                "created_at": response.created_at.isoformat() if response.created_at else None,
                "updated_at": response.updated_at.isoformat() if response.updated_at else None,
            },
            indent=2,
        )

    except Exception as e:
        return f"Error getting user: {e}"


def run_server(transport: str = "stdio", host: str = "localhost", port: int | None = None):
    """Run the MCP server with the specified transport."""
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "http":
        if port is None:
            port = 8000
        # Note: FastMCP may not support HTTP transport directly
        # This is a placeholder for future HTTP transport support
        print(f"HTTP transport not yet implemented. Would run on {host}:{port}")
        mcp.run(transport="stdio")  # Fallback to stdio for now
    else:
        msg = f"Unsupported transport: {transport}"
        raise ValueError(msg)


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codegen server...")
    run_server()
