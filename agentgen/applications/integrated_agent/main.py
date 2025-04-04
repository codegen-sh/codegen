#!/usr/bin/env python3
"""
Main entry point for the integrated agent application.
"""

import argparse
import logging
import os
import sys
import uvicorn
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger("integrated_agent")

# Add the current directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import local modules
from backend.api import app


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Integrated Agent")
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to run the server on (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )
    parser.add_argument(
        "--data-dir",
        default="./data",
        help="Directory to store data in (default: ./data)",
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development",
    )
    return parser.parse_args()


def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Set environment variables
    os.environ["DATA_DIR"] = args.data_dir
    
    # Create data directory if it doesn't exist
    Path(args.data_dir).mkdir(parents=True, exist_ok=True)
    
    # Run the server
    logger.info(f"Starting server on {args.host}:{args.port}")
    uvicorn.run(
        "backend.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()