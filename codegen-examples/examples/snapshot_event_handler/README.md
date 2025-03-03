# Event Handler with codebase snapshotting

This project is designed to using Modal snapshotting to provide parsed codebase instances with minimal latency, make it more manageable to write event based handlers. 

Follow the instructions below to set up and deploy the application.

## Prerequisites

Before you begin, ensure you have the following installed and configured:

1. **uv**: A tool for managing virtual environments and syncing dependencies.
2. **Modal**: Ensure you have Modal configured on your system.

## Setup Instructions

1. **Create a Virtual Environment**

   Use `uv` to create a virtual environment with Python 3.13:

   ```bash
   uv venv --python 3.13

   source ./venv/bin/activate
   ```

2. **Sync Dependencies**

   Sync the project dependencies using `uv`:

   ```bash
   uv sync
   ```

3. **Deploy to Modal**

   Deploy the application to Modal by running:

   ```bash
   uv run modal deploy event_handlers.py
   ```

   This command will deploy the Modal app and provide a web URL for your webhook sync.

## Project Structure

- `event_handlers.py`: Contains the main logic for handling events.
- `pr_tasks.py`: Additional tasks related to pull requests.
- `.env.template` and `.env`: Environment variable templates and configurations.
- `pyproject.toml`: Project configuration and dependencies.


## Integration

Once deployed, you can use the deployed web_url as the webhook endpoint for your slack, linear, or github webhooks.