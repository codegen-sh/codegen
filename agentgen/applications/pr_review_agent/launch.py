#!/usr/bin/env python3
"""
Launch script for the PR Review Bot.
"""

import os
import sys
import time
import logging
import argparse
import json
import threading
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv
import uvicorn
from github import Github

# Import local modules
from webhook_manager import WebhookManager
from ngrok_manager import NgrokManager
from helpers import get_github_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("pr_review_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pr_review_bot")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--use-ngrok", action="store_true", help="Use ngrok to expose the server")
    parser.add_argument("--webhook-url", type=str, help="Webhook URL to use (overrides ngrok)")
    return parser.parse_args()

def load_env():
    """Load environment variables from .env file."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Check for required environment variables
    if not os.environ.get("GITHUB_TOKEN"):
        logger.error("GITHUB_TOKEN environment variable is required")
        print("\n❌ GITHUB_TOKEN environment variable is required")
        print("Please create a .env file with your GitHub token")
        print("Example: GITHUB_TOKEN=ghp_your_token_here")
        sys.exit(1)

def monitor_ip_changes(webhook_manager, ngrok_manager, interval=300):
    """Monitor for IP changes and update webhooks if needed."""
    logger.info("Starting IP change monitor")
    print("\n🔄 Starting IP change monitor...")
    
    last_url = ngrok_manager.get_public_url()
    
    while True:
        try:
            time.sleep(interval)
            current_url = ngrok_manager.get_public_url()
            
            if current_url != last_url:
                logger.info(f"IP changed from {last_url} to {current_url}")
                print(f"\n🔄 IP changed from {last_url} to {current_url}")
                
                # Update all webhooks with the new URL
                webhook_manager.webhook_url = current_url
                webhook_manager.setup_webhooks_for_all_repos()
                last_url = current_url
        except Exception as e:
            logger.error(f"Error in IP monitor: {e}")
            print(f"\n❌ Error in IP monitor: {e}")

def main():
    """Main entry point for the PR Review Bot."""
    # Parse command line arguments
    args = parse_args()
    
    # Load environment variables
    load_env()
    
    # Get GitHub token
    github_token = os.environ.get("GITHUB_TOKEN")
    
    # Initialize GitHub client
    github_client = get_github_client(github_token)
    
    # Set up ngrok if requested
    webhook_url = args.webhook_url
    ngrok_manager = None
    
    if args.use_ngrok and not webhook_url:
        print("\n🔄 Starting ngrok tunnel...")
        try:
            ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN")
            ngrok_manager = NgrokManager(args.port, auth_token=ngrok_auth_token)
            webhook_url = ngrok_manager.start_tunnel()
            
            if not webhook_url:
                logger.error("Failed to start ngrok tunnel")
                print("\n❌ Failed to start ngrok tunnel")
                sys.exit(1)
                
            print(f"\n✅ Ngrok tunnel started at {webhook_url}")
        except Exception as e:
            logger.error(f"Error starting ngrok: {e}")
            print(f"\n❌ Error starting ngrok: {e}")
            sys.exit(1)
    
    # Set up webhook manager
    webhook_manager = WebhookManager(github_client, webhook_url or f"http://localhost:{args.port}/webhook")
    
    # Set up webhooks for all repositories
    print("\n🔄 Setting up webhooks for all repositories...")
    try:
        webhook_manager.setup_webhooks_for_all_repos()
        print("\n✅ Webhooks set up successfully")
    except Exception as e:
        logger.error(f"Error setting up webhooks: {e}")
        print(f"\n❌ Error setting up webhooks: {e}")
    
    # Start IP change monitor if using ngrok
    if ngrok_manager:
        monitor_thread = threading.Thread(
            target=monitor_ip_changes,
            args=(webhook_manager, ngrok_manager),
            daemon=True
        )
        monitor_thread.start()
    
    # Start the server
    print(f"\n🚀 Starting server on port {args.port}...")
    try:
        # Import app here to avoid circular imports
        import app as app_module
        uvicorn.run(app_module.app, host="0.0.0.0", port=args.port)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
