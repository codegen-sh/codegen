# Codegen Agents - Python SDK

This module provides a Python client for interacting with the Codegen AI agents API.

## Installation

The Codegen Agent SDK is included as part of the Codegen package. Ensure you have the latest version installed:

```bash
pip install codegen
```

## Usage

### Basic Example

```python
from codegen.agents.agent import Agent

# Initialize the Agent with your organization ID and API token
agent = Agent(
    org_id="11",  # Your organization ID
    token="your_api_token_here",  # Your API authentication token
    base_url="https://codegen-sh-rest-api.modal.run",  # Optional - defaults to this URL
)

# Run an agent with a prompt
task = agent.run(prompt="Which github repos can you currently access?")

# Check the initial status
print(task.status)  # Returns the current status of the task (e.g., "queued", "in_progress", etc.)

# Refresh the task to get updated status
task.refresh()

# Check the updated status
print(task.status)

# Once task is complete, you can access the result
if task.status == "completed":
    print(task.result)
```

### Agent Class

The `Agent` class is the main entry point for interacting with Codegen AI agents:

```python
Agent(token: str, org_id: Optional[int] = None, base_url: Optional[str] = CODEGEN_BASE_API_URL)
```

Parameters:

- `token` (required): Your API authentication token
- `org_id` (optional): Your organization ID. If not provided, defaults to environment variable `CODEGEN_ORG_ID` or "1"
- `base_url` (optional): API base URL. Defaults to "https://codegen-sh-rest-api.modal.run"

### Methods

#### run()

```python
run(prompt: str) -> AgentTask
```

Runs an agent with the given prompt.

Parameters:

- `prompt` (required): The instruction for the agent to execute

Returns:

- An `AgentTask` object representing the running task

#### get_status()

```python
get_status() -> Optional[Dict[str, Any]]
```

Gets the status of the current task.

Returns:

- A dictionary containing task status information (`id`, `status`, `result`), or `None` if no task has been run

### AgentTask Class

The `AgentTask` class represents a running or completed agent task:

#### Attributes

- `id`: The unique identifier for the task
- `org_id`: The organization ID
- `status`: Current status of the task (e.g., "queued", "in_progress", "completed", "failed")
- `result`: The task result (available when status is "completed")

#### Methods

##### refresh()

```python
refresh() -> None
```

Refreshes the task status from the API.

## Environment Variables

- `CODEGEN_ORG_ID`: Default organization ID (used if `org_id` is not provided)

## Error Handling

Handle potential API errors using standard try/except blocks:

```python
try:
    task = agent.run(prompt="Your prompt here")
    task.refresh()
    print(task.status)
except Exception as e:
    print(f"Error: {e}")
```
