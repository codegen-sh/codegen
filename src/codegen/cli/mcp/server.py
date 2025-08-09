import json
import os
from typing import Annotated, Any

import requests
from fastmcp import Context, FastMCP

# Import API client components
try:
    from codegen_api_client import ApiClient, Configuration
    from codegen_api_client.api import AgentsApi, OrganizationsApi, UsersApi
    from codegen_api_client.models import CreateAgentRunInput

    API_CLIENT_AVAILABLE = True
except ImportError:
    API_CLIENT_AVAILABLE = False

# Import our own API utilities
from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token

# Initialize FastMCP server
mcp = FastMCP(
    "codegen-mcp",
    instructions="MCP server for the Codegen platform. Use the tools and resources to interact with Codegen APIs and manage your development workflow.",
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


def execute_tool_via_api(tool_name: str, arguments: dict):
    """Execute a tool via the Codegen API."""
    try:
        token = get_current_token()
        if not token:
            return {"error": "Not authenticated. Please run 'codegen login' first."}

        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/11/tools/execute"

        payload = {"tool_name": tool_name, "arguments": arguments}

        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()

        return response.json()

    except Exception as e:
        return {"error": f"Error executing tool {tool_name}: {e}"}


def register_dynamic_tools(available_tools: list):
    """Register all available tools from the API as individual MCP tools."""
    import inspect

    for tool_info in available_tools:
        tool_name = tool_info.get("name", "unknown_tool")
        tool_description = tool_info.get("description", "No description available")
        tool_parameters = tool_info.get("parameters", {})

        # Parse the parameter schema
        properties = tool_parameters.get("properties", {})
        required = tool_parameters.get("required", [])

        def make_tool_function(name: str, description: str, props: dict, req: list):
            # Create function dynamically with proper parameters
            def create_dynamic_function():
                # Build parameter list for the function
                param_list = []
                param_annotations = {}

                # Collect required and optional parameters separately
                required_params = []
                optional_params = []

                # Add other parameters from schema
                for param_name, param_info in props.items():
                    param_type = param_info.get("type", "string")
                    param_desc = param_info.get("description", f"Parameter {param_name}").replace("'", '"')
                    is_required = param_name in req

                    # Special handling for tool_call_id - always make it optional
                    if param_name == "tool_call_id":
                        optional_params.append("tool_call_id: Annotated[str, 'Unique identifier for this tool call'] = 'mcp_call'")
                        continue

                    # Convert JSON schema types to Python types
                    if param_type == "string":
                        py_type = "str"
                    elif param_type == "integer":
                        py_type = "int"
                    elif param_type == "number":
                        py_type = "float"
                    elif param_type == "boolean":
                        py_type = "bool"
                    elif param_type == "array":
                        items_type = param_info.get("items", {}).get("type", "string")
                        if items_type == "string":
                            py_type = "list[str]"
                        else:
                            py_type = "list"
                    else:
                        py_type = "str"  # Default fallback

                    # Handle optional parameters (anyOf with null)
                    if "anyOf" in param_info:
                        py_type = f"{py_type} | None"
                        if not is_required:
                            default_val = param_info.get("default", "None")
                            if isinstance(default_val, str) and default_val != "None":
                                default_val = f'"{default_val}"'
                            optional_params.append(f"{param_name}: Annotated[{py_type}, '{param_desc}'] = {default_val}")
                        else:
                            required_params.append(f"{param_name}: Annotated[{py_type}, '{param_desc}']")
                    elif is_required:
                        required_params.append(f"{param_name}: Annotated[{py_type}, '{param_desc}']")
                    else:
                        # Optional parameter with default
                        default_val = param_info.get("default", "None")
                        if isinstance(default_val, str) and default_val not in ["None", "null"]:
                            default_val = f'"{default_val}"'
                        elif isinstance(default_val, bool):
                            default_val = str(default_val)
                        elif default_val is None or default_val == "null":
                            default_val = "None"
                        optional_params.append(f"{param_name}: Annotated[{py_type}, '{param_desc}'] = {default_val}")

                # Only add tool_call_id if it wasn't already in the schema
                tool_call_id_found = any("tool_call_id" in param for param in optional_params)
                if not tool_call_id_found:
                    optional_params.append("tool_call_id: Annotated[str, 'Unique identifier for this tool call'] = 'mcp_call'")

                # Combine required params first, then optional params
                param_list = required_params + optional_params

                # Create the function code
                params_str = ", ".join(param_list)

                # Create a list of parameter names for the function
                param_names = []
                for param in param_list:
                    # Extract parameter name from the type annotation
                    param_name = param.split(":")[0].strip()
                    param_names.append(param_name)

                param_names_str = repr(param_names)

                func_code = f"""
def tool_function({params_str}) -> str:
    '''Dynamically created tool function: {description}'''
    # Collect all parameters by name to avoid circular references
    param_names = {param_names_str}
    arguments = {{}}

    # Get the current frame's local variables
    import inspect
    frame = inspect.currentframe()
    try:
        locals_dict = frame.f_locals
        for param_name in param_names:
            if param_name in locals_dict:
                value = locals_dict[param_name]
                # Handle None values and ensure JSON serializable
                if value is not None:
                    arguments[param_name] = value
    finally:
        del frame

    # Execute the tool via API
    result = execute_tool_via_api('{name}', arguments)

    # Return formatted result
    return json.dumps(result, indent=2)
"""

                # Execute the function code to create the function
                namespace = {"Annotated": Annotated, "json": json, "execute_tool_via_api": execute_tool_via_api, "inspect": inspect}
                exec(func_code, namespace)
                func = namespace["tool_function"]

                # Set metadata
                func.__name__ = name.replace("-", "_")
                func.__doc__ = description

                return func

            return create_dynamic_function()

        # Create the tool function
        tool_func = make_tool_function(tool_name, tool_description, properties, required)

        # Register with FastMCP using the decorator
        decorated_func = mcp.tool()(tool_func)

        print(f"✅ Registered dynamic tool: {tool_name}")


# ----- RESOURCES -----


@mcp.resource("system://manifest", mime_type="application/json")
def get_service_config() -> dict[str, Any]:
    """Get the service config."""
    return {
        "name": "mcp-codegen",
        "version": "0.1.0",
        "description": "The MCP server for the Codegen platform API integration.",
    }


# ----- STATIC CODEGEN API TOOLS -----


@mcp.tool()
def create_agent_run(
    org_id: Annotated[int, "Organization ID"],
    prompt: Annotated[str, "The prompt/task for the agent to execute"],
    repo_name: Annotated[str | None, "Repository name (optional)"] = None,
    branch_name: Annotated[str | None, "Branch name (optional)"] = None,
    ctx: Context | None = None,
) -> str:
    """Create a new agent run in the specified organization."""
    try:
        _, agents_api, _, _ = get_api_client()

        # Create the input object
        agent_input = CreateAgentRunInput(prompt=prompt)
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
    ctx: Context | None = None,
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
    ctx: Context | None = None,
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
    ctx: Context | None = None,
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
    ctx: Context | None = None,
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


def run_server(transport: str = "stdio", host: str = "localhost", port: int | None = None, available_tools: list | None = None):
    """Run the MCP server with the specified transport."""
    # Register dynamic tools if provided
    if available_tools:
        print("🔧 Registering dynamic tools from API...")
        register_dynamic_tools(available_tools)
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


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codegen server...")
    run_server()
