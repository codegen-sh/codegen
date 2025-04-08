import os
from typing import Any, Optional

from codegen.agents.client.openapi_client.api.agents_api import AgentsApi
from codegen.agents.client.openapi_client.api_client import ApiClient
from codegen.agents.client.openapi_client.configuration import Configuration
from codegen.agents.client.openapi_client.models.agent_run_response import AgentRunResponse
from codegen.agents.client.openapi_client.models.create_agent_run_input import CreateAgentRunInput
from codegen.agents.constants import CODEGEN_BASE_API_URL


class AgentTask:
    """Represents an agent run job."""

    def __init__(self, task_data: AgentRunResponse, api_client: ApiClient, org_id: int):
        self.id = task_data.id
        self.org_id = org_id
        self.status = task_data.status
        self.result = task_data.result
        self.web_url = task_data.web_url
        self._api_client = api_client
        self._agents_api = AgentsApi(api_client)

    def refresh(self) -> None:
        """Refresh the job status from the API."""
        if self.id is None:
            return

        job_data = self._agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get(
            agent_run_id=int(self.id), org_id=int(self.org_id), authorization=f"Bearer {self._api_client.configuration.access_token}"
        )

        # Convert API response to dict for attribute access
        job_dict = {}
        if hasattr(job_data, "__dict__"):
            job_dict = job_data.__dict__
        elif isinstance(job_data, dict):
            job_dict = job_data

        self.status = job_dict.get("status")
        self.result = job_dict.get("result")


class Agent:
    """API client for interacting with Codegen AI agents."""

    def __init__(self, token: str, org_id: Optional[int] = None, base_url: Optional[str] = CODEGEN_BASE_API_URL):
        """Initialize a new Agent client.

        Args:
            token: API authentication token
            org_id: Optional organization ID. If not provided, default org will be used.
        """
        self.token = token
        self.org_id = org_id or int(os.environ.get("CODEGEN_ORG_ID", "1"))  # Default to org ID 1 if not specified

        # Configure API client
        config = Configuration(host=base_url, access_token=token)
        self.api_client = ApiClient(configuration=config)
        self.agents_api = AgentsApi(self.api_client)

        # Current job
        self.current_job = None

    def run(self, prompt: str) -> AgentTask:
        """Run an agent with the given prompt.

        Args:
            prompt: The instruction for the agent to execute

        Returns:
            Job: A job object representing the agent run
        """
        run_input = CreateAgentRunInput(prompt=prompt)
        agent_run_response = self.agents_api.create_agent_run_v1_organizations_org_id_agent_run_post(
            org_id=int(self.org_id), create_agent_run_input=run_input, authorization=f"Bearer {self.token}", _headers={"Content-Type": "application/json"}
        )
        # Convert API response to dict for Job initialization

        job = AgentTask(agent_run_response, self.api_client, self.org_id)
        self.current_job = job
        return job

    def get_status(self) -> Optional[dict[str, Any]]:
        """Get the status of the current job.

        Returns:
            dict: A dictionary containing job status information,
                  or None if no job has been run.
        """
        if self.current_job:
            self.current_job.refresh()
            return {"id": self.current_job.id, "status": self.current_job.status, "result": self.current_job.result, "web_url": self.current_job.web_url}
        return None
