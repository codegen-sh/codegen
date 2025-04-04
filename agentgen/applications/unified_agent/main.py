"""
Main module for the unified agent application.
This module provides the entry point for the application.
"""

import os
import sys
import logging
import argparse
import uvicorn
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Unified Agent Application")
    parser.add_argument("--port", type=int, default=8000, help="Port to run the server on")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="Host to run the server on")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--env-file", type=str, default=".env", help="Path to .env file")
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Load environment variables
    load_dotenv(args.env_file)
    
    # Import the API module
    from backend.api import app
    
    # Run the server
    logger.info(f"Starting server on {args.host}:{args.port}")
    uvicorn.run(
        "backend.api:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()