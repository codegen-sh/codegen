# Integrated PR Agent

A CI/CD application that tracks requirements, reviews PRs, and coordinates with Codegen.

## Features

- **Requirements Tracking**: Parse and track requirements from Markdown documents
- **PR Review**: Analyze PRs against requirements and provide feedback
- **Task Orchestration**: Coordinate between requirements and PR reviews
- **Slack Integration**: Communicate with Codegen via Slack
- **GitHub Integration**: Monitor repositories and PRs via GitHub webhooks
- **AI Planning**: Generate project plans and visualize project structure
- **Document Management**: Upload, store, and manage context documents
- **Progress Tracking**: Generate visual progress reports

## Architecture

The Integrated PR Agent consists of the following components:

- **Models**: Data models for requirements, PRs, and documents
- **Services**: Services for interacting with GitHub, Slack, LLMs, and AI planning
- **Task Orchestrator**: Core component that coordinates between requirements and PR reviews
- **API**: FastAPI application for exposing the functionality via HTTP endpoints
- **Web UI**: React-based user interface for managing documents and visualizing progress

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/agentgen/applications/integrated_pr_agent
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Create a `.env` file with the following environment variables:

```
GITHUB_TOKEN=your_github_token
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_CHANNEL_ID=your_slack_channel_id
CODEGEN_USER_ID=codegen_slack_user_id
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key
GITHUB_REPO=owner/repo
DOCS_PATH=path/to/docs
OUTPUT_DIR=output
WEBHOOK_SECRET=your_webhook_secret
```

## Usage

### Running the API Server

```bash
python -m integrated_pr_agent.run api --host 0.0.0.0 --port 8000
```

### Running the Task Orchestrator

```bash
python -m integrated_pr_agent.run orchestrator --repo owner/repo --docs path/to/docs --output output --slack-channel your_slack_channel_id
```

To run the orchestrator once and exit:

```bash
python -m integrated_pr_agent.run orchestrator --repo owner/repo --docs path/to/docs --output output --slack-channel your_slack_channel_id --once
```

## API Endpoints

### Core Endpoints
- `GET /`: Root endpoint
- `POST /webhook`: GitHub webhook endpoint
- `POST /run`: Run the task orchestrator once

### Requirements and PRs
- `GET /requirements`: Get all requirements
- `GET /prs`: Get all pull requests
- `GET /progress`: Get the progress report
- `POST /send-requirement`: Send a specific requirement to Codegen
- `POST /update-requirement-status`: Update the status of a requirement

### Document Management
- `GET /documents`: Get all documents
- `GET /documents/{document_id}`: Get a specific document
- `POST /documents`: Create a new document
- `POST /documents/upload`: Upload a document file
- `DELETE /documents/{document_id}`: Delete a document

### AI Planning
- `POST /generate-project-plan`: Generate a project plan
- `POST /generate-progress-document`: Generate a progress tracking document
- `GET /download/{filename}`: Download a file from the output directory

## Web UI

The Web UI provides a user-friendly interface for:

1. **Document Management**: Upload, view, and delete documents
2. **Repository Configuration**: Configure GitHub repositories
3. **Project Planning**: Generate and visualize project plans
4. **Progress Tracking**: View progress reports and statistics
5. **Requirement Management**: Send requirements to Codegen and track their status

To access the Web UI, navigate to `http://localhost:8000` after starting the API server.

## Development

### Project Structure

```
integrated_pr_agent/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── requirement.py
│   ├── pull_request.py
│   └── document.py
├── services/
│   ├── __init__.py
│   ├── github_service.py
│   ├── requirements_service.py
│   ├── pr_review_service.py
│   ├── slack_service.py
│   └── ai_planning/
│       ├── __init__.py
│       └── planning_service.py
├── api/
│   ├── __init__.py
│   └── app.py
├── task_orchestrator.py
├── run.py
├── requirements.txt
└── README.md
```

## License

MIT