# PR Code Review Agent

A Slack-integrated PR Code Review agent that automatically reviews pull requests against requirements and codebase patterns, and provides feedback via Slack and GitHub.

## Features

- **Automated PR Review**: Analyzes PRs against requirements and codebase patterns
- **Slack Integration**: Communicates with users via Slack
- **GitHub Integration**: Monitors repositories and PRs via GitHub webhooks
- **Planning System**: Creates step-by-step guides from markdown documentation
- **Progress Tracking**: Generates visual progress reports
- **Task Orchestration**: Manages the workflow between planning, PR reviews, and next steps

## Architecture

The PR Code Review agent consists of the following components:

1. **PR Review Agent**: Analyzes PRs against requirements and codebase patterns
2. **Plan Manager**: Creates and manages project plans from markdown documentation
3. **PR Review Handler**: Handles GitHub events and Slack commands
4. **FastAPI Application**: Provides HTTP endpoints for webhooks and API calls

## Installation

1. Clone the repository:

```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen
```

2. Install the dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:

```bash
export GITHUB_TOKEN=your_github_token
export SLACK_BOT_TOKEN=your_slack_bot_token
export SLACK_CHANNEL_ID=your_slack_channel_id
export ANTHROPIC_API_KEY=your_anthropic_api_key  # Optional
export OPENAI_API_KEY=your_openai_api_key  # Optional
export OUTPUT_DIR=output  # Directory for output files
```

## Usage

### Running the Agent

```bash
cd agentgen/applications/pr_code_review
python app.py --host 0.0.0.0 --port 8000 --output-dir output
```

### Setting Up GitHub Webhooks

1. Go to your GitHub repository settings
2. Click on "Webhooks"
3. Click "Add webhook"
4. Set the Payload URL to `https://your-server.com/github/webhook`
5. Set the Content type to `application/json`
6. Select "Let me select individual events"
7. Check "Pull requests"
8. Click "Add webhook"

### Setting Up Slack App

1. Create a new Slack app at https://api.slack.com/apps
2. Add the following OAuth scopes:
   - `chat:write`
   - `app_mentions:read`
   - `channels:history`
   - `channels:read`
3. Install the app to your workspace
4. Set up event subscriptions with the URL `https://your-server.com/slack/events`
5. Subscribe to the `app_mention` event

### Interacting with the Agent via Slack

You can interact with the agent in Slack using the following commands:

- `@pr-review-agent review PR https://github.com/owner/repo/pull/123` - Review a PR
- `@pr-review-agent create plan Title | Description | https://url-to-markdown-file.md` - Create a project plan
- `@pr-review-agent next step` - Get the next step to implement
- `@pr-review-agent progress report` - Get a progress report

## API Endpoints

- `GET /` - Root endpoint
- `POST /github/webhook` - GitHub webhook endpoint
- `POST /slack/events` - Slack events endpoint
- `POST /create-plan` - Create a project plan
- `GET /next-step` - Get the next pending step
- `POST /update-step` - Update the status of a step
- `GET /progress-report` - Generate a progress report

## Development

### Project Structure

```
agentgen/
├── applications/
│   └── pr_code_review/
│       ├── app.py - Main application
│       └── README.md - Documentation
├── backend/
│   ├── agents/
│   │   └── pr_review_agent.py - PR review agent
│   └── extensions/
│       ├── events/
│       │   └── pr_review_handler.py - PR review event handler
│       └── planning/
│           └── manager.py - Project planning manager
```

### Adding New Features

To add new features to the agent:

1. Update the relevant files in the project
2. Add any new dependencies to `requirements.txt`
3. Update the documentation in `README.md`
4. Test the changes locally

## License

MIT
