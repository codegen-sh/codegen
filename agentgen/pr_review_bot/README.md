# PR Review Bot

A GitHub PR review bot that automatically reviews pull requests when triggered by labels or when PRs are opened. The bot analyzes the project's codebase, requirements, and PR contents to provide comprehensive feedback.

## Features

- **Automatic PR Reviews**: Reviews PRs when they are opened or labeled with "review", "codegen", or "pr-review"
- **Documentation Compliance**: Checks if PR changes comply with project documentation
- **Detailed Feedback**: Provides actionable feedback with specific suggestions
- **Webhook Integration**: Easily integrates with GitHub webhooks
- **Ngrok Support**: Includes built-in ngrok support for local development
- **Launch Script**: Simple script to set up and monitor the bot

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pr-review-bot.git
cd pr-review-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create a .env file
touch .env

# Add the following variables
GITHUB_TOKEN=your_github_token
ANTHROPIC_API_KEY=your_anthropic_key  # If using Anthropic models
OPENAI_API_KEY=your_openai_key        # If using OpenAI models
USE_NGROK=true                        # Optional: Use ngrok for webhook tunneling
NGROK_AUTH_TOKEN=your_ngrok_token     # Optional: For ngrok authentication
```

## Usage

### Using the Launch Script

The easiest way to start the bot is with the launch script:

```bash
python launch.py
```

This will:
1. Set up ngrok for webhook tunneling (if enabled)
2. List all connected repositories
3. Set up webhooks for all repositories
4. Start the FastAPI server
5. Monitor webhooks and update them if IP changes

You can also provide a configuration file:

```bash
python launch.py --config config.json
```

### Running the Bot Manually

If you prefer to run the bot without the launch script:

```bash
python app.py
```

If you've enabled ngrok, the bot will automatically create a public URL for your webhook.

### Setting Up GitHub Webhooks

1. Go to your GitHub repository settings
2. Click on "Webhooks" and then "Add webhook"
3. Set the Payload URL to your bot's webhook URL (e.g., `https://your-ngrok-url.ngrok.io/webhook`)
4. Set Content type to `application/json`
5. Select "Let me select individual events" and check "Pull requests"
6. Click "Add webhook"

### Triggering Reviews

The bot will automatically review PRs when:
- A new PR is opened
- A PR is labeled with "review", "codegen", or "pr-review"

You can also manually trigger a review by sending a POST request to:
```
POST /review/{repo_owner}/{repo_name}/{pr_number}
```

## Configuration

You can configure the bot using environment variables or by creating a `config.json` file:

```json
{
  "github_token": "your_github_token",
  "port": 8000,
  "webhook_url": "https://your-webhook-url.com/webhook",
  "use_ngrok": true,
  "ngrok_auth_token": "your_ngrok_token",
  "auto_review": true,
  "auto_merge": false,
  "review_labels": ["review", "codegen", "pr-review"],
  "monitor_interval": 300
}
```

## How It Works

1. The bot receives webhook events from GitHub
2. For PR events, it analyzes the repository's documentation and requirements
3. It then reviews the PR changes against these requirements
4. The bot provides feedback through:
   - PR comments with a summary of findings
   - Inline comments on specific code issues
   - A formal PR review (approve or request changes)
5. If configured, it can automatically merge compliant PRs

## Development

### Project Structure

```
pr_review_bot/
├── app.py                # Main FastAPI application
├── helpers.py            # Core review functionality
├── webhook_manager.py    # GitHub webhook management
├── ngrok_manager.py      # Ngrok tunnel management
├── launch.py             # Launch script for easy setup
├── requirements.txt      # Dependencies
└── README.md             # Documentation
```

### Adding Custom Review Logic

You can extend the review logic by modifying the `analyze_with_codegen` function in `helpers.py`. This function uses LangChain to analyze PRs and can be customized to fit your project's specific requirements.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
