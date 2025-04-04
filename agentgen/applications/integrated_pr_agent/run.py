#!/usr/bin/env python3
"""
Run script for the Integrated PR Agent.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path

import dotenv
import uvicorn

from .task_orchestrator import TaskOrchestrator
from .api.app import app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ],
)
logger = logging.getLogger("integrated_pr_agent")

# Load environment variables
dotenv.load_dotenv()


def run_api(host: str = "0.0.0.0", port: int = 8000):
    """Run the FastAPI application."""
    logger.info(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)


def run_orchestrator(
    repo_name: str,
    docs_path: str,
    output_dir: str,
    slack_channel_id: str = None,
    interval: int = 60,
    once: bool = False,
):
    """Run the task orchestrator."""
    # Create task orchestrator
    orchestrator = TaskOrchestrator(
        repo_name=repo_name,
        docs_path=docs_path,
        output_dir=output_dir,
        slack_channel_id=slack_channel_id,
        github_token=os.environ.get("GITHUB_TOKEN", ""),
        slack_token=os.environ.get("SLACK_BOT_TOKEN", ""),
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        openai_api_key=os.environ.get("OPENAI_API_KEY", ""),
    )
    
    if once:
        logger.info("Running task orchestrator once")
        orchestrator.run_once()
    else:
        logger.info(f"Running task orchestrator continuously with interval {interval} seconds")
        orchestrator.run_continuously(interval=interval)


def main():
    """Main entry point for the application."""
    parser = argparse.ArgumentParser(description="Integrated PR Agent")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # API command
    api_parser = subparsers.add_parser("api", help="Run the API server")
    api_parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    api_parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    
    # Orchestrator command
    orch_parser = subparsers.add_parser("orchestrator", help="Run the task orchestrator")
    orch_parser.add_argument("--repo", required=True, help="GitHub repository (owner/repo)")
    orch_parser.add_argument("--docs", required=True, help="Path to documents directory")
    orch_parser.add_argument("--output", required=True, help="Path to output directory")
    orch_parser.add_argument("--slack-channel", help="Slack channel ID")
    orch_parser.add_argument(
        "--interval", type=int, default=60, help="Interval in seconds for periodic checks"
    )
    orch_parser.add_argument(
        "--once", action="store_true", help="Run once and exit"
    )
    
    args = parser.parse_args()
    
    if args.command == "api":
        run_api(host=args.host, port=args.port)
    elif args.command == "orchestrator":
        run_orchestrator(
            repo_name=args.repo,
            docs_path=args.docs,
            output_dir=args.output,
            slack_channel_id=args.slack_channel,
            interval=args.interval,
            once=args.once,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()