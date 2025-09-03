"""Static Codegen API tools for the MCP server."""

import json
from typing import Annotated

from fastmcp import Context, FastMCP

from ..api_client import get_api_client


def register_static_tools(mcp: FastMCP):
    """Register static Codegen API tools with the MCP server."""

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
            from codegen_api_client.models import CreateAgentRunInput

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
                organizations.append(
                    {
                        "id": org.id,
                        "name": org.name,
                        "slug": org.slug,
                        "created_at": org.created_at.isoformat() if org.created_at else None,
                    }
                )

            return json.dumps(
                {
                    "organizations": organizations,
                    "total": response.total,
                    "page": response.page,
                    "limit": response.limit,
                },
                indent=2,
            )

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
                users.append(
                    {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                    }
                )

            return json.dumps(
                {
                    "users": users,
                    "total": response.total,
                    "page": response.page,
                    "limit": response.limit,
                },
                indent=2,
            )

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
