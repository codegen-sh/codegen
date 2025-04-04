# PR Review Bot Development Scratchpad

## Current Task: Fix Webhook Validation Issues

### Problem
When running the PR review bot, we're encountering webhook validation errors with a 422 status code:
```
Error updating webhook URL for Zeeeepa/arxiver: 422 - Validation Failed
```

### Root Cause Analysis
- The issue is in the `update_webhook_url` method in `webhook_manager.py`
- When updating a webhook, we need to provide all required parameters, not just the URL
- The GitHub API requires the `name` parameter and a complete config object

### Solution
[X] Update the `update_webhook_url` method to create a new config dictionary
[X] Include all required parameters (url, content_type, insecure_ssl, secret)
[X] Set the active parameter to True
[X] Fix the dotenv import in launch.py
[X] Create a proper .env.example file
[X] Update the README.md with comprehensive instructions

### Testing
- Run the bot with `python run.py --use-ngrok`
- Verify that webhooks are properly set up
- Create a test PR to verify the review functionality
- Test the merge functionality

## Next Steps
- Add support for custom review criteria
- Implement more sophisticated analysis techniques
- Add support for other GitHub events
- Improve error handling and logging