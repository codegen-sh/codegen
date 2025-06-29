import os
from typing import Any

from codegen_api_client.api.agents_api import AgentsApi
from codegen_api_client.api_client import ApiClient
from codegen_api_client.configuration import Configuration
from codegen_api_client.models.agent_run_response import AgentRunResponse
from codegen_api_client.models.create_agent_run_input import CreateAgentRunInput
from codegen_api_client.rest import ApiException

from codegen.agents.constants import CODEGEN_BASE_API_URL
from codegen.exceptions import handle_api_error


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
        """Refresh the job status from the API.

        Raises:
            CodegenError: If the API request fails
        """
        if self.id is None:
            return

        try:
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
        except ApiException as e:
            error = handle_api_error(e.status, str(e), getattr(e, "body", None))
            raise error from e

    def is_completed(self) -> bool:
        """Check if the agent task is completed."""
        return self.status in ["completed", "failed", "cancelled"]

    def is_running(self) -> bool:
        """Check if the agent task is currently running."""
        return self.status in ["running", "pending"]

    def is_successful(self) -> bool:
        """Check if the agent task completed successfully."""
        return self.status == "completed"

    def is_failed(self) -> bool:
        """Check if the agent task failed."""
        return self.status == "failed"

    def to_dict(self) -> dict[str, Any]:
        """Convert agent task to dictionary."""
        return {"id": self.id, "org_id": self.org_id, "status": self.status, "result": self.result, "web_url": self.web_url}


class Agent:
    """API client for interacting with Codegen AI agents."""

    def __init__(self, token: str, org_id: int | str | None = None, base_url: str = CODEGEN_BASE_API_URL):
        """Initialize a new Agent client.

        Args:
            token: API authentication token
            org_id: Optional organization ID. If not provided, default org will be used.
            base_url: Base URL for the API (defaults to production)
        """
        self.token = token
        self.org_id = org_id or int(os.environ.get("CODEGEN_ORG_ID", "1"))  # Default to org ID 1 if not specified

        # Configure API client
        config = Configuration(host=base_url, access_token=token)
        self.api_client = ApiClient(configuration=config)
        self.agents_api = AgentsApi(self.api_client)

        # Current job
        self.current_job: AgentTask | None = None

    def run(self, prompt: str) -> AgentTask:
        """Run an agent with the given prompt.

        Args:
            prompt: The instruction for the agent to execute

        Returns:
            AgentTask: A task object representing the agent run

        Raises:
            CodegenError: If the API request fails
        """
        try:
            run_input = CreateAgentRunInput(prompt=prompt)
            agent_run_response = self.agents_api.create_agent_run_v1_organizations_org_id_agent_run_post(
                org_id=int(self.org_id), create_agent_run_input=run_input, authorization=f"Bearer {self.token}", _headers={"Content-Type": "application/json"}
            )

            job = AgentTask(agent_run_response, self.api_client, self.org_id)
            self.current_job = job
            return job
        except ApiException as e:
            error = handle_api_error(e.status, str(e), getattr(e, "body", None))
            raise error from e

    def get_status(self) -> dict[str, Any] | None:
        """Get the status of the current job.

        Returns:
            dict: A dictionary containing job status information,
                  or None if no job has been run.

        Raises:
            CodegenError: If the API request fails
        """
        if self.current_job:
            self.current_job.refresh()
            return {"id": self.current_job.id, "status": self.current_job.status, "result": self.current_job.result, "web_url": self.current_job.web_url}
        return None

    def get_task(self, task_id: int | str) -> AgentTask:
        """Get a specific agent task by ID.

        Args:
            task_id: Agent task ID to retrieve

        Returns:
            AgentTask: The requested agent task

        Raises:
            CodegenError: If the API request fails or task is not found
        """
        try:
            response = self.agents_api.get_agent_run_v1_organizations_org_id_agent_run_agent_run_id_get(org_id=int(self.org_id), agent_run_id=int(task_id), authorization=f"Bearer {self.token}")
            return AgentTask(response, self.api_client, self.org_id)
        except ApiException as e:
            error = handle_api_error(e.status, str(e), getattr(e, "body", None))
            raise error from e
