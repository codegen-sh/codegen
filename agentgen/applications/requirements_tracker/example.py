#!/usr/bin/env python3
"""
Example script to demonstrate how to use the Requirements Tracker application.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from requirements_tracker.app import RequirementsTracker

def main():
    """Run the example."""
    # Set up the environment variables
    os.environ["GITHUB_TOKEN"] = "your_github_token"
    os.environ["SLACK_BOT_TOKEN"] = "your_slack_bot_token"
    os.environ["SLACK_APP_TOKEN"] = "your_slack_app_token"
    os.environ["CODEGEN_USER_ID"] = "codegen_slack_user_id"

    # Create a tracker instance
    tracker = RequirementsTracker(
        repo_name="Zeeeepa/Project-Plan",
        docs_path="path/to/docs",
        output_dir="output",
        slack_channel="your_slack_channel_id",
        interval=60,
    )

    # Run the tracker once
    tracker.run_once()

if __name__ == "__main__":
    main()