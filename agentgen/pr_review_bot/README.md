# GitHub PR Review Bot

A powerful, AI-powered GitHub PR review bot that automatically analyzes pull requests against project documentation and requirements.

## Features

- Automatically reviews PRs when they are created or labeled
- Analyzes code changes against project documentation
- Provides detailed feedback with specific suggestions
- Supports ngrok for local webhook development
- Uses the latest langchain libraries for AI-powered analysis

## Prerequisites

- Python 3.10+ (Python 3.13 recommended)
- GitHub account with a personal access token
- Anthropic API key or OpenAI API key (for AI analysis)
- Ngrok account (optional, for local development)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen
git checkout update-agentgen-langchain
```

### 2. Set up a virtual environment

```bash
# For Python 3.13 (recommended)
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
cd agentgen/pr_review_bot
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the `pr_review_bot` directory:

```bash
cp .env.example .env
```

Edit the `.env` file with your API keys:

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

### Running the bot locally

```bash
python run.py --use-ngrok
```

This will:
1. Start a FastAPI server
2. Set up ngrok for webhook tunneling
3. Set up webhooks for all repositories
4. Start monitoring for PR events

### Running the bot without ngrok

If you have a public URL for your server:

```bash
python run.py --webhook-url https://your-server.com/webhook
```

### Running the bot on a specific port

```bash
python run.py --port 8080 --use-ngrok
```

## How it works

1. The bot sets up webhooks on your GitHub repositories
2. When a PR is created or labeled with "review", the bot is triggered
3. The bot analyzes the PR changes against project documentation
4. The bot provides detailed feedback with specific suggestions
5. If all requirements are met, the bot approves the PR
6. If issues are found, the bot requests changes with detailed feedback

## Customizing the bot

You can customize the bot's behavior by modifying the following files:

- `helpers.py`: Contains the core review logic
- `app.py`: Handles webhook events
- `launch.py`: Sets up the server and webhooks

## Troubleshooting

### Common issues

- **Import errors**: Make sure you're running the bot from the `pr_review_bot` directory
- **Authentication errors**: Check your GitHub token has the correct permissions
- **Webhook errors**: Make sure your ngrok tunnel is running and the webhook URL is correct
- **LLM errors**: Check your Anthropic or OpenAI API key is valid

### Logs

The bot logs all activity to `pr_review_bot.log` in the current directory.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
