# Slack Utilities

This module provides utility functions for working with the Slack API in a safe and reliable way.

## Features

### `safe_add_reaction`

A utility function that safely adds a reaction to a Slack message, handling the case where the reaction already exists.

This function is particularly useful for preventing the `SlackApiError` with the error message `already_reacted` that can occur when trying to add a reaction that already exists on a message.

### Usage

```python
from slack_sdk import WebClient
from codegen.extensions.slack.utils import safe_add_reaction

client = WebClient(token="your-token")

# Safely add a reaction
response = safe_add_reaction(client=client, channel="C12345", timestamp="1234567890.123456", name="thumbsup")

# The function will not raise an exception if the reaction already exists
```

## Error Handling

The `safe_add_reaction` function handles the following error cases:

- If the reaction already exists (`already_reacted` error), it logs the information and returns a success response.
- For all other errors, it logs the error and re-raises the exception for proper handling upstream.
