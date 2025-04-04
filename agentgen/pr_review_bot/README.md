# PR Review Bot

A GitHub PR review bot that automatically reviews pull requests and provides detailed feedback. The bot analyzes PRs against project documentation and requirements, and can automatically merge compliant PRs or ask for user confirmation.

## Features

- Automatically reviews all incoming PRs
- Analyzes PRs against project documentation and requirements
- Provides detailed feedback with specific suggestions
- Can automatically merge compliant PRs
- Asks for user confirmation before merging non-compliant PRs
- Uses ngrok for local webhook development
- Supports both Anthropic and OpenAI models

## Requirements

- Python 3.8+
- GitHub Personal Access Token with repo scope
- Anthropic API key or OpenAI API key
- ngrok (optional, for local development)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen/agentgen/pr_review_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```bash
cp .env.example .env
```

4. Edit the `.env` file with your API keys:
```
# GitHub configuration
GITHUB_TOKEN=your_github_personal_access_token

# LLM API keys (at least one is required)
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key

# Webhook configuration
WEBHOOK_SECRET=your_webhook_secret

# Ngrok configuration (optional)
NGROK_AUTH_TOKEN=your_ngrok_token
```

## Usage

### Running the Bot

To run the bot with ngrok for local development:

```bash
python run.py --use-ngrok
```

To run the bot with a custom webhook URL:

```bash
python run.py --webhook-url https://your-webhook-url.com/webhook
```

To run the bot on a specific port:

```bash
python run.py --port 8080
```

### How It Works

1. The bot starts a FastAPI server to receive GitHub webhook events
2. It sets up webhooks for all repositories you have access to
3. When a PR is created or updated, GitHub sends a webhook event to the bot
4. The bot analyzes the PR against the project's documentation and requirements
5. It posts a detailed review comment on the PR
6. If the PR complies with all requirements, it can automatically merge it
7. If issues are found, it asks for user confirmation before merging

### PR Review Process

The PR review process consists of the following steps:

1. The bot receives a webhook event from GitHub
2. It extracts the PR number and repository name
3. It fetches the PR details and the repository's documentation
4. It analyzes the PR against the documentation using a language model
5. It posts a detailed review comment on the PR
6. It submits a formal review (approve or request changes)
7. It tries to merge the PR if it complies with requirements
8. If issues are found, it asks for user confirmation before merging

## Configuration

### Environment Variables

- `GITHUB_TOKEN`: GitHub Personal Access Token with repo scope
- `ANTHROPIC_API_KEY`: Anthropic API key (optional if using OpenAI)
- `OPENAI_API_KEY`: OpenAI API key (optional if using Anthropic)
- `WEBHOOK_SECRET`: Secret for GitHub webhook signature verification
- `NGROK_AUTH_TOKEN`: ngrok authentication token (optional)

### Command Line Arguments

- `--port`: Port to run the server on (default: 8000)
- `--use-ngrok`: Use ngrok to expose the server
- `--webhook-url`: Webhook URL to use (overrides ngrok)

## Development

### Project Structure

- `app.py`: FastAPI application for webhook handling
- `launch.py`: Main entry point for setup and configuration
- `run.py`: Wrapper script for easy execution
- `helpers.py`: Core PR review functionality
- `webhook_manager.py`: GitHub webhook management
- `ngrok_manager.py`: ngrok tunnel management
- `codebase.py`: Simple GitHub operations wrapper

### Adding Custom Review Criteria

To add custom review criteria, modify the `analyze_with_llm` function in `helpers.py`. You can update the prompt to include specific requirements or checks.

### Extending the Bot

The bot can be extended in various ways:

- Add support for more GitHub events
- Implement custom review criteria
- Add support for other LLM providers
- Implement more sophisticated analysis techniques
- Add support for custom review templates

## Troubleshooting

### Common Issues

- **Webhook setup fails**: Make sure your GitHub token has the `admin:repo_hook` scope
- **ngrok tunnel fails**: Make sure ngrok is installed and your auth token is valid
- **LLM analysis fails**: Make sure your API keys are valid and you have sufficient credits
- **PR review fails**: Make sure the repository has at least one markdown file in the root directory

### Logs

The bot logs to both the console and a file named `pr_review_bot.log`. Check the logs for detailed error messages and debugging information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
