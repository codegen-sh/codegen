#!/usr/bin/env python3
"""
PR Review Bot Launch Script

This script provides a simple way to launch the PR Review Bot with all necessary components:
1. Sets up ngrok for webhook tunneling
2. Lists all connected repositories
3. Updates webhook URLs when IP changes
4. Reviews PRs automatically
"""

import os
import sys
import json
import time
import argparse
import logging
import threading
import subprocess
from typing import Dict, Any, Optional, List
import uvicorn
from fastapi import FastAPI
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("pr_review_bot.log")
    ]
)
logger = logging.getLogger("pr_review_bot")

# Import bot components
try:
    from app import app as fastapi_app, get_config
    from webhook_manager import WebhookManager
    from ngrok_manager import NgrokManager
    from helpers import get_github_client
except ImportError:
    logger.error("Failed to import PR Review Bot components. Make sure you're running from the correct directory.")
    sys.exit(1)

class PRReviewBotLauncher:
    """
    Launcher for the PR Review Bot that handles setup, monitoring, and shutdown.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the launcher.
        
        Args:
            config_path: Path to the configuration file (optional)
        """
        self.config = self._load_config(config_path)
        self.ngrok_manager = None
        self.webhook_url = None
        self.github_client = None
        self.webhook_manager = None
        self.server_thread = None
        self.monitor_thread = None
        self.running = False
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """
        Load configuration from file or environment variables.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
        """
        config = {
            "github_token": os.environ.get("GITHUB_TOKEN", ""),
            "port": int(os.environ.get("PORT", 8000)),
            "webhook_url": os.environ.get("WEBHOOK_URL"),
            "use_ngrok": os.environ.get("USE_NGROK", "true").lower() == "true",
            "ngrok_auth_token": os.environ.get("NGROK_AUTH_TOKEN"),
            "auto_review": os.environ.get("AUTO_REVIEW", "true").lower() == "true",
            "auto_merge": os.environ.get("AUTO_MERGE", "false").lower() == "true",
            "review_labels": os.environ.get("REVIEW_LABELS", "review,codegen,pr-review").split(","),
            "monitor_interval": int(os.environ.get("MONITOR_INTERVAL", 300))  # 5 minutes
        }
        
        # Override with config file if provided
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    logger.info(f"Loaded configuration from {config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration from {config_path}: {e}")
        
        # Validate required configuration
        if not config["github_token"]:
            logger.error("GitHub token not provided. Set the GITHUB_TOKEN environment variable.")
            sys.exit(1)
        
        return config
    
    def setup(self):
        """
        Set up the PR Review Bot components.
        """
        logger.info("Setting up PR Review Bot...")
        
        # Initialize GitHub client
        self.github_client = get_github_client(self.config["github_token"])
        
        # Start ngrok if enabled
        if self.config["use_ngrok"] and not self.config["webhook_url"]:
            logger.info("Starting ngrok tunnel...")
            self.ngrok_manager = NgrokManager(
                self.config["port"], 
                auth_token=self.config["ngrok_auth_token"]
            )
            self.webhook_url = self.ngrok_manager.start_tunnel()
            
            if not self.webhook_url:
                logger.warning("Failed to start ngrok tunnel. Webhooks may not work correctly.")
                logger.warning("Consider setting WEBHOOK_URL manually or fixing ngrok installation.")
        else:
            self.webhook_url = self.config["webhook_url"]
        
        # Initialize webhook manager
        if self.webhook_url:
            self.webhook_manager = WebhookManager(self.github_client, self.webhook_url)
            logger.info(f"Webhook URL: {self.webhook_url}")
        else:
            logger.warning("No webhook URL available. The bot will only respond to manual requests.")
        
        logger.info("PR Review Bot setup completed")
    
    def list_repositories(self) -> List[str]:
        """
        List all repositories connected to the GitHub token.
        
        Returns:
            List of repository names
        """
        if not self.github_client:
            logger.error("GitHub client not initialized")
            return []
        
        try:
            repos = list(self.github_client.get_user().get_repos())
            repo_names = [repo.full_name for repo in repos]
            logger.info(f"Found {len(repo_names)} repositories")
            return repo_names
        except Exception as e:
            logger.error(f"Error listing repositories: {e}")
            return []
    
    def setup_webhooks(self):
        """
        Set up webhooks for all repositories.
        """
        if not self.webhook_manager:
            logger.error("Webhook manager not initialized")
            return
        
        try:
            logger.info("Setting up webhooks for all repositories...")
            results = self.webhook_manager.setup_webhooks_for_all_repos()
            logger.info(f"Webhook setup completed for {len(results)} repositories")
            
            # Print results
            for repo_name, status in results.items():
                logger.info(f"Repository {repo_name}: {status}")
        except Exception as e:
            logger.error(f"Error setting up webhooks: {e}")
    
    def monitor_webhooks(self):
        """
        Monitor webhooks and update them if necessary.
        This runs in a separate thread.
        """
        if not self.webhook_manager:
            logger.error("Webhook manager not initialized")
            return
        
        logger.info("Starting webhook monitor...")
        
        while self.running:
            try:
                # Check if ngrok URL has changed
                if self.ngrok_manager:
                    current_url = self.ngrok_manager.public_url
                    if current_url and current_url != self.webhook_url:
                        logger.info(f"Ngrok URL changed from {self.webhook_url} to {current_url}")
                        self.webhook_url = current_url
                        self.webhook_manager.webhook_url = f"{current_url}/webhook"
                        
                        # Update all webhooks
                        logger.info("Updating webhooks with new URL...")
                        self.setup_webhooks()
                
                # Sleep for the configured interval
                time.sleep(self.config["monitor_interval"])
            except Exception as e:
                logger.error(f"Error in webhook monitor: {e}")
                time.sleep(60)  # Sleep for a minute before retrying
    
    def start_server(self):
        """
        Start the FastAPI server in a separate thread.
        """
        def run_server():
            uvicorn.run(fastapi_app, host="0.0.0.0", port=self.config["port"])
        
        self.server_thread = threading.Thread(target=run_server)
        self.server_thread.daemon = True
        self.server_thread.start()
        logger.info(f"Server started on port {self.config['port']}")
    
    def start(self):
        """
        Start the PR Review Bot.
        """
        logger.info("Starting PR Review Bot...")
        self.running = True
        
        # Setup components
        self.setup()
        
        # List repositories
        repos = self.list_repositories()
        print("\n📋 Connected Repositories:")
        for repo in repos:
            print(f"  - {repo}")
        
        # Setup webhooks
        if self.webhook_manager:
            self.setup_webhooks()
        
        # Start the server
        self.start_server()
        
        # Start the webhook monitor
        self.monitor_thread = threading.Thread(target=self.monitor_webhooks)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logger.info("PR Review Bot started successfully")
        print("\n✅ PR Review Bot is running!")
        print(f"   Server: http://localhost:{self.config['port']}")
        if self.webhook_url:
            print(f"   Webhook URL: {self.webhook_url}")
        print("\nPress Ctrl+C to stop the bot")
        
        try:
            # Keep the main thread alive
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """
        Stop the PR Review Bot.
        """
        logger.info("Stopping PR Review Bot...")
        self.running = False
        
        # Stop ngrok
        if self.ngrok_manager:
            self.ngrok_manager.stop_tunnel()
        
        logger.info("PR Review Bot stopped")
        print("\n👋 PR Review Bot stopped")

def main():
    """
    Main entry point for the launch script.
    """
    parser = argparse.ArgumentParser(description="Launch the PR Review Bot")
    parser.add_argument("--config", help="Path to configuration file")
    args = parser.parse_args()
    
    # Print banner
    print("\n" + "=" * 60)
    print("🤖 PR Review Bot Launcher")
    print("=" * 60)
    
    # Start the launcher
    launcher = PRReviewBotLauncher(args.config)
    launcher.start()

if __name__ == "__main__":
    main()
