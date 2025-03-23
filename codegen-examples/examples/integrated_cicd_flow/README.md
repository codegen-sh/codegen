# Integrated CI/CD Flow with Codegen

This example demonstrates a complete CI/CD flow using Codegen components. It integrates several examples into a cohesive workflow:

1. **Requirements & Planning Hub** (Linear + AI)
   - Captures and analyzes requirements from Linear
   - Breaks down complex tasks into manageable subtasks
   - Creates a development plan with dependencies

2. **AI-Assisted Development** (Local Checkout + Ticket-to-PR)
   - Checks out code locally for development
   - Uses AI to generate code changes based on requirements
   - Creates PRs with detailed documentation

3. **Comprehensive Code Review** (PR Review + Deep Analysis)
   - Reviews PRs with multiple perspectives (style, security, performance)
   - Performs deep code analysis to validate changes
   - Provides feedback via GitHub and Slack

4. **Continuous Knowledge & Assistance** (Slack Integration)
   - Provides context and assistance throughout the pipeline
   - Answers questions about the codebase and development process
   - Facilitates team communication and knowledge sharing

## Architecture

```
[Linear] → [Planning Hub] → [Development Agent] → [GitHub PR] → [Review Bot] → [Slack Notifications]
```

## Setup

1. Create a `.env` file with your credentials:

```
# Linear
LINEAR_ACCESS_TOKEN="your_token"
LINEAR_SIGNING_SECRET="your_secret"
LINEAR_TEAM_ID="your_team_id"

# GitHub
GITHUB_TOKEN="your_github_token"

# AI Providers
ANTHROPIC_API_KEY="your_anthropic_key"
OPENAI_API_KEY="your_openai_key"

# Slack
SLACK_SIGNING_SECRET="your_slack_secret"
SLACK_BOT_TOKEN="your_slack_token"
```

2. Deploy the components:

```bash
# Deploy the Planning Hub
modal deploy planning_hub.py

# Deploy the Development Agent
modal deploy development_agent.py

# Deploy the Review Bot
modal deploy review_bot.py

# Deploy the Slack Assistant
modal deploy slack_assistant.py
```

3. Configure webhooks:
   - Linear: Use the Planning Hub URL
   - GitHub: Use the Review Bot URL
   - Slack: Use the Slack Assistant URL

## Components

- `planning_hub.py`: Analyzes Linear tickets and creates development plans
- `development_agent.py`: Generates code changes and creates PRs
- `review_bot.py`: Reviews PRs and provides feedback
- `slack_assistant.py`: Provides assistance and notifications via Slack
- `shared/`: Contains shared utilities and models