# PR Review Bot Development Scratchpad

## Current Task: Fix PR Review Bot to Work Without Package Installation

### Task Description
The PR review bot needs to be updated to work without requiring the agentgen package to be installed. This involves:
1. Updating imports to use relative imports
2. Creating a simple wrapper script that adds the parent directory to the Python path
3. Simplifying the Codebase class to not depend on codegen
4. Using langchain directly instead of agentgen wrappers

### Progress
[X] Update app.py to use relative imports
[X] Update launch.py to use relative imports
[X] Create run.py wrapper script
[X] Update helpers.py to use langchain directly
[X] Create a simplified Codebase class
[X] Update README.md with clear instructions
[X] Create .env.example file
[X] Update requirements.txt

### Next Steps
- Test the PR review bot locally
- Verify webhook handling
- Test ngrok integration
- Test PR review functionality

## Notes

### Local Development Setup
- Use run.py to start the bot
- Set up ngrok for webhook tunneling
- Configure GitHub webhooks to point to the ngrok URL

### PR Review Process
1. PR is created or labeled
2. Webhook event is received
3. PR is analyzed against documentation
4. Review comment is posted
5. Formal review is submitted

### LLM Integration
- Using langchain_anthropic.ChatAnthropic for Claude models
- Using langchain_openai.ChatOpenAI for GPT models
- Simple prompt template for PR analysis