# PR Review Bot Development Scratchpad

## Current Task
Update the PR review bot to check all PRs and handle merging with user confirmation.

## Progress
- [X] Fix webhook_manager.py to properly update webhook URLs
- [X] Fix launch.py to use the correct dotenv import
- [X] Update app.py to review all PRs regardless of label
- [X] Ensure helpers.py has merge functionality with user confirmation
- [X] Create .env.example with all required environment variables
- [X] Update requirements.txt with all dependencies
- [X] Create run.py wrapper script for easy execution

## Next Steps
- [ ] Test the PR review bot with a real PR
- [ ] Add more documentation on how to use the bot
- [ ] Consider adding support for custom review criteria

## Implementation Notes
- The webhook_manager.py file had a bug in the update_webhook_url method that was causing the "Hook.edit() missing 1 required positional argument: 'name'" error.
- The app.py file was updated to review all PRs regardless of label.
- The helpers.py file already had merge functionality with user confirmation.
- The launch.py file was fixed to use the correct dotenv import.
- The ngrok_manager.py file was updated to add the missing get_public_url method.

## Usage
```bash
# Navigate to the PR review bot directory
cd agentgen/pr_review_bot

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your API keys

# Run the bot
python run.py --use-ngrok
```