# PR Review Bot

An AI-powered GitHub PR review bot that automatically reviews pull requests and provides detailed feedback. The bot analyzes PRs against project documentation and requirements, and can automatically merge compliant PRs or ask for user confirmation.

## Features

- Automatically reviews all incoming PRs
- Analyzes PRs against project documentation and requirements
- Provides detailed feedback with specific suggestions
- Automatically merges compliant PRs
- Asks for user confirmation before merging non-compliant PRs
- Supports ngrok for local webhook development

## Requirements

- Python 3.12+
- GitHub token with repo and webhook permissions
- Anthropic API key or OpenAI API key
- Ngrok authentication token (for local development)

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
   GITHUB_TOKEN=your_github_token
   ANTHROPIC_API_KEY=your_anthropic_key
   OPENAI_API_KEY=your_openai_key
   WEBHOOK_SECRET=your_webhook_secret
   NGROK_AUTH_TOKEN=your_ngrok_token
   ```

## Usage

### Running the Bot

To run the bot with ngrok for webhook tunneling:

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
4. The bot analyzes the PR against project documentation and requirements
5. It provides detailed feedback with specific suggestions
6. If the PR complies with requirements, it automatically merges it
7. If issues are found, it asks for user confirmation before merging

### Webhook Setup

The bot automatically sets up webhooks for all repositories you have access to. If you're using ngrok, the webhook URL will be automatically updated when your IP changes.

If you want to manually set up webhooks:

1. Go to your repository settings
2. Click on "Webhooks"
3. Click "Add webhook"
4. Set the Payload URL to `https://your-webhook-url.com/webhook`
5. Set the Content type to `application/json`
6. Select "Let me select individual events"
7. Check "Pull requests"
8. Click "Add webhook"

## Development

### Project Structure

- `app.py`: FastAPI application for webhook handling
- `launch.py`: Main entry point for setup and configuration
- `run.py`: Wrapper script that adds the current directory to the Python path
- `helpers.py`: Core PR review functionality using LangChain
- `webhook_manager.py`: GitHub webhook management
- `ngrok_manager.py`: Ngrok tunnel management for local development
- `codebase.py`: Simple GitHub operations wrapper

### Adding New Features

To add new features to the bot:

1. Update the relevant files in the project
2. Add any new dependencies to `requirements.txt`
3. Update the documentation in `README.md`
4. Test the changes locally

## Troubleshooting

### Common Issues

- **Webhook validation errors**: Make sure your webhook URL is publicly accessible and the webhook secret is correct.
- **API key errors**: Check that your GitHub token and LLM API keys are correct in the `.env` file.
- **Import errors**: Make sure you're running the bot from the correct directory and have installed all dependencies.

### Logs

The bot logs all activity to `pr_review_bot.log`. Check this file for detailed error messages and debugging information.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
