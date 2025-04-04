# Requirements Tracker

A CI/CD application that tracks project requirements, analyzes implementation progress, and coordinates with Codegen to complete tasks.

## Overview

Requirements Tracker is designed to:

1. Parse project requirements from Markdown documents
2. Analyze GitHub repositories to track implementation progress
3. Generate step-by-step task lists with progress indicators
4. Communicate with Codegen via Slack to request implementations
5. Validate PR changes against requirements
6. Provide visual feedback on project progress

## Features

- **Markdown Parser**: Extracts structured requirements from Markdown files
- **GitHub Integration**: Analyzes repositories to track implementation progress
- **Progress Tracking**: Maintains a task list with completion status
- **Slack Integration**: Communicates with Codegen to request implementations
- **PR Validation**: Validates PR changes against requirements
- **Visual Dashboard**: Provides a visual representation of project progress

## Usage

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Create a `.env` file with the following variables:

```
GITHUB_TOKEN=your_github_token
SLACK_BOT_TOKEN=your_slack_bot_token
SLACK_APP_TOKEN=your_slack_app_token
CODEGEN_USER_ID=codegen_slack_user_id
```

### Running the Application

```bash
python app.py --repo owner/repo --docs path/to/docs --output output_dir
```

### Command Line Arguments

- `--repo`: GitHub repository to analyze (owner/repo)
- `--docs`: Path to directory containing Markdown documents
- `--output`: Path to directory for output files
- `--slack-channel`: Slack channel ID for communication (optional)
- `--interval`: Interval in minutes for periodic checks (optional, default: 60)

## Integration with Codegen

Requirements Tracker integrates with Codegen through Slack to:

1. Send implementation requests based on requirements
2. Receive implementation proposals
3. Validate implementations against requirements
4. Track progress and update task lists

## Example Workflow

1. Parse requirements from Markdown documents
2. Analyze repository to determine current implementation status
3. Generate a task list with progress indicators
4. Send implementation requests to Codegen via Slack
5. Validate PR changes against requirements
6. Update task list and progress indicators
7. Repeat until all requirements are implemented

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.