# PR Review Bot

An AI-powered GitHub PR review bot that automatically reviews pull requests against project documentation and requirements.

## Features

- Automatically reviews PRs when opened or labeled
- Analyzes PRs against project documentation
- Provides detailed feedback with specific suggestions
- Supports both automatic and manual review triggers
- Includes ngrok support for local webhook development

## Installation

### Prerequisites

- Python 3.12 or higher
- GitHub account with a personal access token
- Anthropic API key (optional, for Claude models)
- OpenAI API key (optional, for GPT models)
- Ngrok account with auth token (optional, for local development)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/yourusername/your-repo.git
cd your-repo
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the agentgen package:

```bash
pip install -e .
```

4. Install the PR review bot dependencies:

```bash
cd agentgen/pr_review_bot
pip install -r requirements.txt
```

5. Create a `.env` file in the `agentgen/pr_review_bot` directory (you can copy from `.env.example`):

```
GITHUB_TOKEN=your_github_token
ANTHROPIC_API_KEY=your_anthropic_key
OPENAI_API_KEY=your_openai_key
WEBHOOK_SECRET=your_webhook_secret
NGROK_AUTH_TOKEN=your_ngrok_token
```

## Usage

### Running the Bot

To start the PR review bot:

```bash
cd agentgen/pr_review_bot
python launch.py
```

This will:
1. Set up ngrok for webhook tunneling (if configured)
2. List all connected repositories
3. Set up webhooks for all repositories
4. Start the FastAPI server

### Command Line Options

The launch script supports several command line options:

```
python launch.py --help
```

- `--port PORT`: Port to run the server on (default: 8000)
- `--no-ngrok`: Disable ngrok tunnel
- `--no-webhooks`: Disable webhook setup
- `--webhook-url URL`: Custom webhook URL

### Triggering Reviews

The bot can be triggered in several ways:

1. **Automatically on PR creation**: The bot will review new PRs when they are created
2. **By adding a label**: Add the "review", "codegen", or "pr-review" label to a PR
3. **Manually via API**: Send a POST request to `/review/{owner}/{repo}/{pr_number}`

### Webhook Setup

For the bot to receive GitHub events, you need to set up webhooks. This can be done automatically by the launch script or manually in the GitHub repository settings:

1. Go to your repository on GitHub
2. Click on "Settings" > "Webhooks" > "Add webhook"
3. Set the Payload URL to your bot's webhook URL (e.g., `https://your-ngrok-url.ngrok.io/webhook`)
4. Set the Content type to `application/json`
5. Select "Let me select individual events" and choose "Pull requests"
6. Click "Add webhook"

## Configuration

The bot can be configured using environment variables or command line arguments:

- `GITHUB_TOKEN`: GitHub personal access token (required)
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude models
- `OPENAI_API_KEY`: OpenAI API key for GPT models
- `WEBHOOK_SECRET`: Secret for GitHub webhook validation
- `NGROK_AUTH_TOKEN`: Ngrok authentication token

## Development

### Project Structure

- `app.py`: FastAPI application with webhook handlers
- `helpers.py`: Core PR review functionality
- `launch.py`: Launch script for the bot
- `webhook_manager.py`: GitHub webhook management
- `ngrok_manager.py`: Ngrok tunnel management
- `codebase.py`: Simple Codebase class for GitHub operations

### Adding Custom Review Logic

To customize the review logic, modify the `analyze_with_codegen` function in `helpers.py`. This function uses the ChatAgent to analyze PRs and generate review comments.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
