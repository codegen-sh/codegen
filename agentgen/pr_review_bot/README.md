# AI-Powered Pull Request Review Bot

This project demonstrates how to build an intelligent GitHub PR review bot that automatically reviews pull requests. The bot uses agentgen's GitHub integration and AI capabilities to provide comprehensive code reviews with actionable feedback.

## Features

- **Automatic PR Review**: Reviews all incoming PRs automatically
- **Codebase Analysis**: Analyzes the project's structure, requirements, and coding standards
- **Contextual Feedback**: Provides specific, line-by-line feedback on code changes
- **Summary Reports**: Generates comprehensive review summaries
- **Actionable Insights**: Suggests concrete improvements and identifies potential issues

## How It Works

The PR review bot follows this workflow:

1. **Event Handling**: Listens for GitHub webhook events when PRs are created or updated
2. **Codebase Analysis**: Analyzes the repository to understand its structure and requirements
3. **PR Review**: Examines the PR changes and evaluates them against best practices
4. **Feedback Generation**: Provides both inline comments and a summary review
5. **Result Reporting**: Logs the review results and notifies developers

## Prerequisites

Before running this application, you'll need:

- GitHub API Token with repository access
- Anthropic API Key (for Claude models) or OpenAI API Key

## Setup

1. Clone the repository
2. Set up your environment variables in a `.env` file:

```env
GITHUB_TOKEN=your_github_token
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key (optional)
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Deployment

Run the bot using FastAPI:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

This will create a webhook endpoint that you can configure in your GitHub repository settings.

## GitHub Webhook Configuration

1. Go to your repository settings
2. Navigate to "Webhooks" and click "Add webhook"
3. Set the Payload URL to your endpoint (e.g., `https://your-server.com/github/webhook`)
4. Set the Content type to `application/json`
5. Select "Let me select individual events" and choose "Pull requests"
6. Click "Add webhook"

## Customization

You can customize the bot's behavior by modifying:

- `app.py`: Configure event handling and webhook setup
- `helpers.py`: Adjust the review logic and feedback generation
- Environment variables: Set different API keys or configuration options

## Dependencies

This project uses the following key dependencies:

- `langchain` and related packages for AI agent functionality
- `fastapi` for webhook handling
- `PyGithub` for GitHub API integration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
