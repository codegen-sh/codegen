#!/usr/bin/env python3
"""
Simple wrapper script to run the PR Review Bot without package installation.
This script adds the current directory to the Python path so that local imports work.
"""

import os
import sys
import argparse

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Now we can import from the launch module directly
from launch import main

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--use-ngrok", action="store_true", help="Use ngrok to expose the server")
    parser.add_argument("--webhook-url", type=str, help="Webhook URL to use (overrides ngrok)")
    
    # Parse arguments and pass them to the main function directly
    args = parser.parse_args()
    
    # Run the main function
    main()