# PR Review Bot

A GitHub PR review bot that automatically reviews pull requests when triggered by labels or when PRs are opened. The bot analyzes the project's codebase, requirements, and PR contents to provide comprehensive feedback.

## Features

- Automatically reviews all incoming PRs
- Analyzes the project's codebase and requirements
- Provides detailed feedback on code changes
- Generates a comprehensive review summary
- Logs results and insights in the terminal
- Supports webhook integration for real-time PR reviews

## Installation

### Prerequisites

- Python 3.12+ (recommended)
- GitHub token with repo and admin:repo_hook scopes

### Setup

1. Clone the repository:

```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen
```

2. Check out the branch:

```bash
git config remote.origin.fetch "+refs/heads/*:refs/remotes/origin/*"
git fetch --unshallow --all
git checkout update-agentgen-langchain
```

3. Create a virtual environment:

```bash
# For Python 3.13 (using deadsnakes PPA)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev

# Create and activate the virtual environment
python3.13 -m venv venv
source venv/bin/activate
```

4. Install dependencies:

```bash
cd agentgen/pr_review_bot
pip install -r requirements.txt
```

5. Create a `.env` file:

```bash
cp .env.example .env
```

6. Edit the `.env` file with your API keys:

```
# GitHub token with repo and admin:repo_hook scopes
GITHUB_TOKEN=your_github_token

# LLM API keys (at least one is required)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Webhook secret for GitHub webhooks (optional but recommended)
WEBHOOK_SECRET=your_webhook_secret

# Ngrok authentication token (optional, for local development)
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

The bot automatically sets up webhooks for all repositories accessible by your GitHub token. If you're using ngrok, the webhook URL will be automatically updated when your IP changes.

## How It Works

1. When a PR is opened or labeled with "review", the bot is triggered
2. The bot analyzes the PR changes against the project's codebase and requirements
3. It generates a comprehensive review with actionable feedback
4. The review is posted as a comment on the PR
5. If the PR meets all requirements, it's approved
6. If issues are found, the bot provides insights in the terminal

## Development

### Project Structure

- `app.py`: FastAPI application for handling webhooks
- `launch.py`: Main entry point for the PR review bot
- `helpers.py`: Core PR review functionality
- `webhook_manager.py`: GitHub webhook management
- `ngrok_manager.py`: Ngrok tunnel management
- `run.py`: Simple wrapper script for running the bot

### Adding Custom Review Logic

To customize the review logic, modify the `review_pr` function in `helpers.py`. You can add additional checks, such as:

- Code style validation
- Security vulnerability scanning
- Performance analysis
- Documentation requirements

## Troubleshooting

### Common Issues

- **Webhook Setup Fails**: Ensure your GitHub token has the `admin:repo_hook` scope
- **Ngrok Tunnel Fails**: Check your ngrok authentication token and installation
- **LLM API Errors**: Verify your API keys in the `.env` file
- **Import Errors**: Make sure you're running the bot from the correct directory

### Logs

The bot logs all activity to `pr_review_bot.log` in the current directory. Check this file for detailed error messages and debugging information.

## License

MIT
