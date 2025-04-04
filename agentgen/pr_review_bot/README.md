# PR Review Bot

A GitHub PR review bot that automatically reviews pull requests against project documentation and requirements.

## Features

- Analyzes PRs against project documentation
- Provides detailed feedback with specific suggestions
- Supports both automatic and manual review triggers
- Includes ngrok support for local webhook development
- Uses the latest langchain libraries

## Installation

### Prerequisites

- Python 3.12 or higher
- GitHub account with a personal access token
- Anthropic API key (Claude) or OpenAI API key (GPT-4)
- Ngrok account (optional, for local development)

### Setup

1. Clone the repository:

```bash
git clone https://github.com/Zeeeepa/codegen.git
cd codegen
```

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
cd agentgen/pr_review_bot
pip install -r requirements.txt
```

4. Create a `.env` file:

```bash
cp .env.example .env
```

5. Edit the `.env` file with your API keys:

```
GITHUB_TOKEN=your_github_token
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
2. Set up ngrok for webhook tunneling (if `--use-ngrok` is specified)
3. Set up webhooks for all repositories accessible by your GitHub token
4. Start monitoring for PR events

### Command Line Options

- `--port PORT`: Port to run the server on (default: 8000)
- `--use-ngrok`: Use ngrok to expose the server
- `--webhook-url URL`: Webhook URL to use (overrides ngrok)

### Triggering Reviews

The bot can be triggered in several ways:

1. **Automatically** when a PR is opened or updated
2. **By label** when a PR is labeled with "review", "codegen", or "pr-review"
3. **Manually** by calling the API endpoint:

```
POST /review/{repo_owner}/{repo_name}/{pr_number}
```

### Review Process

When triggered, the bot will:

1. Analyze the PR against project documentation
2. Check if the changes comply with requirements
3. Provide detailed feedback with specific suggestions
4. Post a comment on the PR with the review results
5. Submit a formal review (approve or request changes)

## Development

### Project Structure

- `app.py`: FastAPI application with webhook handlers
- `launch.py`: Main entry point for the bot
- `helpers.py`: Helper functions for PR review
- `codebase.py`: Simple Codebase class for GitHub operations
- `webhook_manager.py`: GitHub webhook management
- `ngrok_manager.py`: Ngrok tunnel management

### Adding Custom Review Logic

To customize the review logic, modify the `analyze_with_llm` function in `helpers.py`. This function uses a language model to analyze PRs against documentation.

## Troubleshooting

### Common Issues

- **Webhook setup fails**: Make sure your GitHub token has the `admin:repo_hook` scope
- **LLM API errors**: Check your API keys in the `.env` file
- **Ngrok errors**: Make sure your ngrok authtoken is valid

### Logs

Logs are written to `pr_review_bot.log` in the current directory. Check this file for detailed error messages.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
