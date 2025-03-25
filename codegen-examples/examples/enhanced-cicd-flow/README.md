# Enhanced CI/CD Flow with Codegen

This example demonstrates a cohesive CI/CD workflow that integrates multiple Codegen components to create a seamless development experience from requirements to deployment.

## Architecture Overview

```
[Requirements] → [Planning] → [Development] → [Review] → [Testing] → [Deployment] → [Monitoring]
```

### Components

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

## Setup Instructions

1. Clone this repository
2. Create a `.env` file with the required credentials (see `.env.template`)
3. Deploy the components using Modal

```bash
# Deploy the components
modal deploy requirements_hub.py
modal deploy development_assistant.py
modal deploy code_review.py
modal deploy knowledge_assistant.py
```

## Usage

1. Create a ticket in Linear with the "Codegen" label
2. The Requirements Hub will analyze the ticket and create a development plan
3. The Development Assistant will generate code changes and create a PR
4. The Code Review component will review the PR and provide feedback
5. The Knowledge Assistant will answer questions and provide context throughout the process

## Environment Variables

```
# Linear
LINEAR_ACCESS_TOKEN="your_token"
LINEAR_SIGNING_SECRET="your_secret"
LINEAR_TEAM_ID="your_team_id"

# GitHub
GITHUB_TOKEN="your_github_token"

# Slack
SLACK_SIGNING_SECRET="your_slack_secret"
SLACK_BOT_TOKEN="your_slack_token"

# AI Providers
ANTHROPIC_API_KEY="your_anthropic_key"
OPENAI_API_KEY="your_openai_key"
```