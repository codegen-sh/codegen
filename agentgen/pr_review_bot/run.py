#!/usr/bin/env python3
"""
Simple wrapper script to run the PR Review Bot without package installation.
This script adds the parent directory to the Python path so that local imports work.
"""

import os
import sys
import argparse

# Add the parent directory to the Python path
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Now we can import from the pr_review_bot package
from pr_review_bot.launch import main

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--use-ngrok", action="store_true", help="Use ngrok to expose the server")
    parser.add_argument("--webhook-url", type=str, help="Webhook URL to use (overrides ngrok)")
    
    # Parse arguments and pass them to sys.argv
    args = parser.parse_args()
    sys.argv = [sys.argv[0]]
    if args.port:
        sys.argv.extend(["--port", str(args.port)])
    if args.use_ngrok:
        sys.argv.append("--use-ngrok")
    if args.webhook_url:
        sys.argv.extend(["--webhook-url", args.webhook_url])
    
    # Run the main function
    main()