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
from pathlib import Path

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
    parser.add_argument("--frontend-dir", type=str, default="frontend/build", help="Path to frontend build directory")
    return parser.parse_args()

def main():
    """Main entry point for the application."""
    args = parse_args()
    
    # Load environment variables
    load_dotenv(args.env_file)
    
    # Import the API module
    from backend.api import app
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse
    
    # Set up frontend serving
    frontend_dir = Path(__file__).parent / args.frontend_dir
    if frontend_dir.exists():
        logger.info(f"Serving frontend from {frontend_dir}")
        app.mount("/static", StaticFiles(directory=str(frontend_dir / "static")), name="static")
        
        @app.get("/{path:path}", include_in_schema=False)
        async def serve_frontend(path: str):
            # If path is an API endpoint, let it be handled by the API
            if path.startswith("api/"):
                return None
                
            # Otherwise, serve the frontend
            file_path = frontend_dir / path
            if file_path.exists() and file_path.is_file():
                return FileResponse(str(file_path))
            return FileResponse(str(frontend_dir / "index.html"))
    else:
        logger.warning(f"Frontend directory {frontend_dir} does not exist. Frontend will not be served.")
    
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