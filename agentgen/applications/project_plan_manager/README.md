# Unified Agent Application

This application integrates multiple agent functionalities into a single unified interface, including:

- PR review agent
- Requirements tracking
- Project planning
- Slack integration
- Workflow visualization

## Features

- **Unified Configuration**: All environment variables can be configured through the UI settings dialog
- **Workflow Visualization**: Track the progress of workflows with a visual interface
- **PR Review**: Automatically review PRs based on requirements and codebase context
- **Requirements Tracking**: Track requirements and their implementation status
- **Project Planning**: Create and manage project plans
- **Slack Integration**: Communicate with the agent through Slack

## Installation

1. Clone the repository
2. Install the backend dependencies:

```bash
pip install -r requirements.txt
```

3. Install the frontend dependencies:

```bash
cd frontend
npm install
```

4. Create a `.env` file with the required environment variables (or configure them through the UI)

## Usage

### Development Mode

1. Start the backend:

```bash
python main.py --reload
```

2. Start the frontend development server:

```bash
cd frontend
npm start
```

3. Open the UI in your browser at `http://localhost:3000`

### Production Mode

1. Build the frontend:

```bash
cd frontend
npm run build
```

2. Start the application:

```bash
python main.py
```

3. Open the UI in your browser at `http://localhost:8000`
4. Configure the settings through the UI
5. Start using the agent!

## Environment Variables

All environment variables can be configured through the UI settings dialog. Here are the available settings:

### Slack Configuration

- `SLACK_BOT_TOKEN`: Slack bot token
- `SLACK_APP_TOKEN`: Slack app token
- `SLACK_CHANNEL_ID`: Slack channel ID
- `CODEGEN_USER_ID`: Codegen user ID

### GitHub Configuration

- `GITHUB_TOKEN`: GitHub token
- `GITHUB_REPO`: GitHub repository
- `WEBHOOK_SECRET`: GitHub webhook secret
- `NGROK_AUTH_TOKEN`: Ngrok auth token
- `NGROK_DOMAIN`: Ngrok domain

### AI Provider Configuration

- `ANTHROPIC_API_KEY`: Anthropic API key
- `OPENAI_API_KEY`: OpenAI API key

### Application Configuration

- `DATA_DIR`: Data directory
- `DOCS_PATH`: Documentation path
- `OUTPUT_DIR`: Output directory
- `PORT`: Application port
- `INTERVAL`: Check interval in seconds

## API Endpoints

The application provides a RESTful API for interacting with the agent. Here are the available endpoints:

### Settings

- `GET /settings`: Get all settings
- `PUT /settings`: Update all settings
- `GET /settings/slack`: Get Slack settings
- `PUT /settings/slack`: Update Slack settings
- `GET /settings/github`: Get GitHub settings
- `PUT /settings/github`: Update GitHub settings
- `GET /settings/ai`: Get AI settings
- `PUT /settings/ai`: Update AI settings
- `GET /settings/app`: Get application settings
- `PUT /settings/app`: Update application settings
- `GET /settings/workflow`: Get workflow settings
- `PUT /settings/workflow`: Update workflow settings
- `POST /settings/test-slack-connection`: Test Slack connection

### Workflows

- `POST /workflows`: Create a new workflow
- `GET /workflows`: Get all workflows
- `GET /workflows/{workflow_id}`: Get a workflow by ID
- `PUT /workflows/{workflow_id}`: Update a workflow
- `DELETE /workflows/{workflow_id}`: Delete a workflow
- `POST /workflows/{workflow_id}/start`: Start a workflow
- `POST /workflows/{workflow_id}/complete`: Complete a workflow
- `POST /workflows/{workflow_id}/fail`: Fail a workflow
- `POST /workflows/{workflow_id}/cancel`: Cancel a workflow
- `PUT /workflows/{workflow_id}/steps/{step_id}`: Update a workflow step
- `POST /workflows/{workflow_id}/steps/{step_id}/complete`: Complete a workflow step
- `POST /workflows/{workflow_id}/steps/{step_id}/fail`: Fail a workflow step
- `POST /workflows/{workflow_id}/steps/{step_id}/skip`: Skip a workflow step

### PR Reviews

- `POST /pr-reviews`: Create a new PR review
- `GET /pr-reviews`: Get all PR reviews
- `GET /pr-reviews/{pr_review_id}`: Get a PR review by ID
- `PUT /pr-reviews/{pr_review_id}`: Update a PR review
- `DELETE /pr-reviews/{pr_review_id}`: Delete a PR review

### Requirements

- `POST /requirements`: Create a new requirement
- `GET /requirements`: Get all requirements
- `GET /requirements/{requirement_id}`: Get a requirement by ID
- `PUT /requirements/{requirement_id}`: Update a requirement
- `DELETE /requirements/{requirement_id}`: Delete a requirement

### Project Plans

- `POST /project-plans`: Create a new project plan
- `GET /project-plans`: Get all project plans
- `GET /project-plans/{project_plan_id}`: Get a project plan by ID
- `PUT /project-plans/{project_plan_id}`: Update a project plan
- `DELETE /project-plans/{project_plan_id}`: Delete a project plan

## License

This project is licensed under the MIT License - see the LICENSE file for details.