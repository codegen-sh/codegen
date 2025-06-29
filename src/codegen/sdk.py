"""Unified Codegen SDK providing access to all API functionality."""

import os
from typing import Optional, Union

from codegen.agents import Agent
from codegen.organizations import Organizations
from codegen.users import Users
from codegen.agents.constants import CODEGEN_BASE_API_URL


class CodegenSDK:
    """Unified SDK for interacting with the Codegen API.
    
    This class provides convenient access to all Codegen API functionality
    including agents, organizations, and users management.
    
    Example:
        ```python
        from codegen import CodegenSDK
        
        # Initialize the SDK
        sdk = CodegenSDK(token="your-api-token")
        
        # Use agents
        task = sdk.agents.run("Create a new feature")
        
        # List organizations
        orgs = sdk.organizations.list()
        
        # Get users in an organization
        users = sdk.users(org_id=1).list()
        ```
    """
    
    def __init__(self, token: str, org_id: Optional[Union[int, str]] = None, base_url: str = CODEGEN_BASE_API_URL):
        """Initialize the Codegen SDK.
        
        Args:
            token: API authentication token
            org_id: Default organization ID for operations that require it
            base_url: Base URL for the API (defaults to production)
        """
        self.token = token
        self.org_id = org_id or int(os.environ.get("CODEGEN_ORG_ID", "1"))
        self.base_url = base_url
        
        # Initialize API clients
        self._agents = Agent(token=token, org_id=self.org_id, base_url=base_url)
        self._organizations = Organizations(token=token, base_url=base_url)
    
    @property
    def agents(self) -> Agent:
        """Access to the Agents API.
        
        Returns:
            Agent: Agent API client for running and managing agent tasks
        """
        return self._agents
    
    @property
    def organizations(self) -> Organizations:
        """Access to the Organizations API.
        
        Returns:
            Organizations: Organizations API client for managing organizations
        """
        return self._organizations
    
    def users(self, org_id: Optional[Union[int, str]] = None) -> Users:
        """Access to the Users API for a specific organization.
        
        Args:
            org_id: Organization ID to scope user operations to.
                   If not provided, uses the default org_id from SDK initialization.
        
        Returns:
            Users: Users API client for managing users in the specified organization
        """
        target_org_id = org_id or self.org_id
        return Users(token=self.token, org_id=target_org_id, base_url=self.base_url)
    
    def set_default_org(self, org_id: Union[int, str]) -> None:
        """Set the default organization ID for SDK operations.
        
        Args:
            org_id: Organization ID to use as default
        """
        self.org_id = org_id
        # Update the agents client with the new org_id
        self._agents = Agent(token=self.token, org_id=self.org_id, base_url=self.base_url)
