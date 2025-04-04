# PR Review Bot

A GitHub PR review bot that automatically reviews pull requests when triggered by labels or events. The bot analyzes the project's codebase, requirements, and PR contents to provide comprehensive code reviews with actionable feedback.

## Features

- Automatically reviews all incoming PRs
- Analyzes the project's codebase and requirements
- Provides detailed feedback with specific suggestions
- Supports webhook-based event handling
- Includes ngrok support for local development
- Uses the latest langchain libraries for AI-powered reviews

## Installation

### Prerequisites

- Python 3.12 or higher
- GitHub account with repository access
- GitHub personal access token with repo and admin:repo_hook scopes
- Anthropic API key and/or OpenAI API key

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen
```

2. Check out the branch:
```bash
git checkout update-agentgen-langchain
```

3. Navigate to the PR review bot directory:
```bash
cd agentgen/pr_review_bot
```

4. Install dependencies:
```bash
pip install -r requirements.txt
```

5. Create a `.env` file:
```bash
cp .env.example .env
```

6. Edit the `.env` file with your API keys:
```
GITHUB_TOKEN=your_github_personal_access_token
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
WEBHOOK_SECRET=your_webhook_secret
NGROK_AUTH_TOKEN=your_ngrok_token
```

## Usage

### Running the Bot

To run the PR review bot:

```bash
python run.py --use-ngrok
```

This will:
1. Start a FastAPI server
2. Set up ngrok for webhook tunneling (if configured)
3. Set up webhooks for all repositories
4. Start monitoring for PR events

### Command Line Options

- `--port`: Port to run the server on (default: 8000)
- `--use-ngrok`: Use ngrok to expose the server
- `--webhook-url`: Webhook URL to use (overrides ngrok)

### Webhook Setup

The bot automatically sets up webhooks for all repositories you have access to. If you want to manually set up webhooks:

1. Go to your repository settings
2. Click on "Webhooks"
3. Add a new webhook
4. Set the Payload URL to your server URL (e.g., ngrok URL)
5. Set the Content type to `application/json`
6. Set the Secret to your `WEBHOOK_SECRET`
7. Select "Let me select individual events" and choose "Pull requests"
8. Click "Add webhook"

## How It Works

1. When a PR is created or updated, GitHub sends a webhook event to the bot
2. The bot analyzes the PR against the project's codebase and requirements
3. If all requirements are met, the bot confirms the PR and prints confirmation in the terminal
4. If issues are found, the bot prints insights and suggestions in the terminal

## Development

### Project Structure

- `app.py`: FastAPI application for webhook handling
- `launch.py`: Main entry point for the PR review bot
- `run.py`: Wrapper script for easy execution
- `helpers.py`: Helper functions for PR review
- `webhook_manager.py`: GitHub webhook management
- `ngrok_manager.py`: Ngrok tunnel management
- `codebase.py`: Simple codebase class for GitHub operations

### Adding New Features

To add new features to the PR review bot:

1. Update the relevant files
2. Add new dependencies to `requirements.txt` if needed
3. Update the documentation in `README.md`
4. Test the changes locally

## License

MIT
