# AI-Powered Pull Request Review Bot

This example project demonstrates how to deploy an agentic bot that automatically reviews GitHub Pull Requests. The bot analyzes code changes and their dependencies to provide comprehensive code reviews using AI, considering both direct modifications and their impact on the codebase.

## Prerequisites

Before running this application, you'll need the following API tokens and credentials:

- GitHub API Token
- Anthropic API Token
- GitHub Repository Access

## Setup

1. Clone the repository
1. Set up your environment variables in a `.env` file:

```env
GITHUB_TOKEN=your_github_token
ANTHROPIC_API_KEY=your_anthropic_token
GITHUB_REPO_OWNER=your_repo_owner
GITHUB_REPO_NAME=your_repo_name
GITHUB_PR_NUMBER=your_pr_number
```

## Features

- Automated PR code review using AI
- Deep dependency analysis of code changes
- Context-aware feedback generation
- Structured review format with actionable insights
- Integration with GitHub PR system

## Usage

1. `uv sync`
1. `uv run modal deploy app.py`
   - This will deploy a modal app that can be triggered to review PRs
1. Create or update a PR to trigger the review bot

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
