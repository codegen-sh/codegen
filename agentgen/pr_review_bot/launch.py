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
from pyngrok import ngrok

from webhook_manager import WebhookManager
from ngrok_manager import NgrokManager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="pr_review_bot.log",
    filemode="a"
)
logger = logging.getLogger("pr_review_bot")

console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console.setFormatter(formatter)
logger.addHandler(console)

def load_env_file():
    """Load environment variables from .env file."""
    try:
        # Try to load from .env file
        load_dotenv()
        
        required_vars = ["GITHUB_TOKEN"]
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            print(f"\n❌ Error: Missing required environment variables: {', '.join(missing_vars)}")
            print("Please create a .env file with the following variables:")
            print("GITHUB_TOKEN=your_github_token")
            print("ANTHROPIC_API_KEY=your_anthropic_key (optional)")
            print("OPENAI_API_KEY=your_openai_key (optional)")
            print("WEBHOOK_SECRET=your_webhook_secret (optional)")
            print("NGROK_AUTH_TOKEN=your_ngrok_token (optional)")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading .env file: {e}")
        print(f"\n❌ Error loading .env file: {e}")
        sys.exit(1)

def get_github_client() -> Github:
    """Get a GitHub client instance."""
    token = os.environ.get("GITHUB_TOKEN", "")
    return Github(token)

def list_repositories(github_client: Github) -> List[Dict[str, Any]]:
    """List all repositories accessible by the GitHub token."""
    repos = []
    
    print("\n📋 Listing accessible repositories:")
    
    try:
        for repo in github_client.get_user().get_repos():
            repos.append({
                "name": repo.name,
                "full_name": repo.full_name,
                "url": repo.html_url,
                "private": repo.private,
                "description": repo.description
            })
            print(f"  - {repo.full_name} {'🔒' if repo.private else '🌐'}")
    except Exception as e:
        logger.error(f"Error listing repositories: {e}")
        print(f"\n❌ Error listing repositories: {e}")
    
    return repos

def setup_ngrok(port: int) -> Optional[str]:
    """Set up ngrok tunnel for webhook URL."""
    ngrok_auth_token = os.environ.get("NGROK_AUTH_TOKEN")
    
    if not ngrok_auth_token:
        print("\n⚠️ No NGROK_AUTH_TOKEN found in environment variables.")
        print("Webhooks will only work if your server is publicly accessible.")
        return None
    
    print("\n🔄 Setting up ngrok tunnel...")
    
    try:
        ngrok_manager = NgrokManager(port, auth_token=ngrok_auth_token)
        webhook_url = ngrok_manager.start_tunnel()
        
        if webhook_url:
            print(f"\n✅ Ngrok tunnel established: {webhook_url}")
            return webhook_url
        else:
            print("\n❌ Failed to establish ngrok tunnel.")
            return None
    except Exception as e:
        logger.error(f"Error setting up ngrok: {e}")
        print(f"\n❌ Error setting up ngrok: {e}")
        return None

def setup_webhooks(github_client: Github, webhook_url: str):
    """Set up webhooks for all repositories."""
    print("\n🔄 Setting up webhooks for repositories...")
    
    webhook_manager = WebhookManager(
        github_client,
        webhook_url
    )
    
    try:
        result = webhook_manager.setup_webhooks_for_all_repos()
        print(f"\n✅ Webhook setup completed for {len(result)} repositories")
    except Exception as e:
        logger.error(f"Error setting up webhooks: {e}")
        print(f"\n❌ Error setting up webhooks: {e}")

def start_server(port: int):
    """Start the FastAPI server."""
    print(f"\n🚀 Starting server on port {port}...")
    
    try:
        from app import app
        uvicorn.run(app, host="0.0.0.0", port=port)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

def monitor_ip_changes(github_client: Github, webhook_url: str, check_interval: int = 300):
    """Monitor for IP changes and update webhooks if needed."""
    print("\n🔄 Starting IP change monitor...")
    
    webhook_manager = WebhookManager(
        github_client,
        webhook_url
    )
    
    while True:
        try:
            current_url = webhook_url
            if current_url != webhook_url:
                print(f"\n🔄 Webhook URL changed: {webhook_url} -> {current_url}")
                webhook_url = current_url
                webhook_manager.webhook_url = current_url
                webhook_manager.update_webhooks_for_all_repos()
        except Exception as e:
            logger.error(f"Error in IP change monitor: {e}")
        
        time.sleep(check_interval)

def main():
    """Main entry point for the PR Review Bot."""
    parser = argparse.ArgumentParser(description="PR Review Bot")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--no-ngrok", action="store_true", help="Disable ngrok tunnel")
    parser.add_argument("--no-webhooks", action="store_true", help="Disable webhook setup")
    parser.add_argument("--webhook-url", type=str, help="Custom webhook URL")
    args = parser.parse_args()
    
    load_env_file()
    
    print("\n🤖 PR Review Bot")
    print("===============")
    
    github_client = get_github_client()
    
    repositories = list_repositories(github_client)
    
    webhook_url = args.webhook_url
    if not webhook_url and not args.no_ngrok:
        webhook_url = setup_ngrok(args.port)
    
    if not webhook_url:
        webhook_url = f"http://localhost:{args.port}/webhook"
        print(f"\n⚠️ Using local webhook URL: {webhook_url}")
        print("This will only work if your server is publicly accessible.")
    
    if not args.no_webhooks and webhook_url:
        setup_webhooks(github_client, webhook_url)
    
    if not args.no_ngrok and webhook_url and not args.webhook_url:
        monitor_thread = threading.Thread(
            target=monitor_ip_changes,
            args=(github_client, webhook_url),
            daemon=True
        )
        monitor_thread.start()
    
    start_server(args.port)

if __name__ == "__main__":
    main()
