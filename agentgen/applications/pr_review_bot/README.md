# AI-Powered Pull Request Review Bot

This project implements an AI-powered bot that automatically reviews GitHub Pull Requests. The bot analyzes code changes and their dependencies to provide comprehensive code reviews using AI, considering both direct modifications and their impact on the codebase. It can also automatically merge valid PRs to the main branch.

## Features

- Automated PR code review using AI
- Deep dependency analysis of code changes
- Context-aware feedback generation
- Structured review format with actionable insights
- Integration with GitHub PR system
- Automatic merging of valid PRs
- Webhook support for all repositories
- Ngrok integration for local development

## Prerequisites

Before running this application, you'll need the following:

- GitHub API Token with `repo` and `admin:repo_hook` scopes
- Anthropic API Token (recommended) or OpenAI API Token
- Ngrok account and auth token (for local development)
- Python 3.10 or higher

## Setup

1. Clone the repository
2. Navigate to the PR review bot directory:
   ```
   cd agentgen/applications/pr_review_bot
   ```
3. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. Install dependencies:
   ```
   pip install -e .
   ```
5. Create a `.env` file based on the `.env.example` template:
   ```
   cp .env.example .env
   ```
6. Edit the `.env` file with your API tokens and configuration

## Usage

### Running Locally with Ngrok

To run the bot locally with Ngrok for webhook forwarding:

```bash
python run.py --use-ngrok
```

This will:
1. Start a local server
2. Create an Ngrok tunnel to expose it to the internet
3. Set up webhooks for all your GitHub repositories
4. Start listening for PR events

### Running with a Custom Webhook URL

If you already have a publicly accessible URL:

```bash
python run.py --webhook-url https://your-domain.com/webhook
```

### Running on a Custom Port

```bash
python run.py --port 9000 --use-ngrok
```

## How It Works

1. The bot sets up webhooks on your GitHub repositories
2. When a PR is created or updated, GitHub sends a webhook event
3. The bot processes the event and analyzes the PR
4. It uses Codegen's AI capabilities to review the code
5. The review is posted as comments on the PR
6. If the PR is valid, it can be automatically merged

## Webhook Events

The bot responds to the following GitHub webhook events:

- `pull_request:opened` - When a new PR is created
- `pull_request:synchronize` - When a PR is updated with new commits
- `pull_request:reopened` - When a closed PR is reopened
- `pull_request:labeled` - When a PR is labeled (specifically for the "Codegen" label)
- `pull_request:unlabeled` - When a label is removed from a PR

## Configuration

The bot can be configured through environment variables in the `.env` file:

- `GITHUB_TOKEN` - GitHub API token
- `WEBHOOK_SECRET` - Secret for GitHub webhook verification
- `NGROK_AUTH_TOKEN` - Ngrok authentication token
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models
- `OPENAI_API_KEY` - OpenAI API key (fallback if Anthropic is not available)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.