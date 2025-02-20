# Linear Ticket to GitHub PR Bot

This example project demonstrates how to deploy an agentic bot that automatically creates GitHub Pull Requests from Linear tickets. The bot leverages Linear's webhook system to listen for ticket updates and uses AI to generate corresponding GitHub PRs with appropriate code changes.

## Prerequisites

Before running this application, you'll need the following API tokens and credentials:

- GitHub API Token
- Linear API Token
- Anthropic API Token
- Linear Signing Key
- Linear Team ID

## Setup

1. Clone the repository
1. Set up your environment variables in a `.env` file:

```env
GITHUB_TOKEN=your_github_token
LINEAR_API_TOKEN=your_linear_token
ANTHROPIC_API_KEY=your_anthropic_token
LINEAR_SIGNING_KEY=your_linear_signing_key
LINEAR_TEAM_ID=your_team_id
```

## Features

- Automatic PR creation from Linear tickets
- AI-powered code generation using an agentic approach
- Webhook integration with Linear

## Usage

1. uv sync
1. uv run modal deploy app.py
   - At this point you should have a modal app with an endpoint that is auto registered to linear as a webhook callback url.
1. Try making a ticket and adding the `Codegen` label to trigger the agent

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
