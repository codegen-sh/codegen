# Integrated PR Agent

A CI/CD application that tracks requirements, reviews PRs, and coordinates with Codegen.

## Features

- **Requirements Tracking**: Parse and track requirements from Markdown documents
- **PR Review**: Analyze PRs against requirements and provide feedback
- **Task Orchestration**: Coordinate between requirements and PR reviews
- **Slack Integration**: Communicate with Codegen via Slack
- **GitHub Integration**: Monitor repositories and PRs via GitHub webhooks

## Architecture

The Integrated PR Agent consists of the following components:

- **Models**: Data models for requirements and PRs
- **Services**: Services for interacting with GitHub, Slack, and LLMs
- **Task Orchestrator**: Core component that coordinates between requirements and PR reviews
- **API**: FastAPI application for exposing the functionality via HTTP endpoints

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

- `GET /`: Root endpoint
- `POST /webhook`: GitHub webhook endpoint
- `POST /run`: Run the task orchestrator once
- `GET /requirements`: Get all requirements
- `GET /prs`: Get all pull requests
- `GET /progress`: Get the progress report
- `POST /send-requirement`: Send a specific requirement to Codegen
- `POST /update-requirement-status`: Update the status of a requirement

## Development

### Project Structure

```
integrated_pr_agent/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── requirement.py
│   └── pull_request.py
├── services/
│   ├── __init__.py
│   ├── github_service.py
│   ├── requirements_service.py
│   ├── pr_review_service.py
│   └── slack_service.py
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