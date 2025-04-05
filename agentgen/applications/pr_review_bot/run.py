#!/usr/bin/env python3
"""
Run script for the PR Review Bot.
This script adds the current directory to the Python path and runs the launch script.
"""

import os
import sys
import argparse

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Add the agentgen directory to the Python path
agentgen_dir = os.path.abspath(os.path.join(current_dir, "../.."))
sys.path.insert(0, agentgen_dir)

def main():
    """Main entry point for the run script."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--use-ngrok", action="store_true", help="Use ngrok to expose the server")
    parser.add_argument("--webhook-url", type=str, help="Webhook URL to use (overrides ngrok)")
    args = parser.parse_args()
    
    # Import the launch script
    from launch import main as launch_main
    
    # Run the launch script
    launch_main()

if __name__ == "__main__":
    main()
