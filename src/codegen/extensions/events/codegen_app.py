import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from .github import GitHub
from .linear import Linear
from .slack import Slack

logger = logging.getLogger(__name__)


class CodegenApp:
    """A FastAPI-based application for handling various code-related events."""

    def __init__(self, name: str, modal_api_key: Optional[str] = None):
        self.name = name
        self._modal_api_key = modal_api_key

        # Create the FastAPI app
        self.app = FastAPI(title=name)

        # Initialize event handlers
        self.linear = Linear(self)
        self.slack = Slack(self)
        self.github = GitHub(self)

        # Register routes
        self._setup_routes()

    def _setup_routes(self):
        """Set up the FastAPI routes for different event types."""

        @self.app.get("/", response_class=HTMLResponse)
        async def root():
            """Render the main page."""
            return """
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Codegen</title>
                    <style>
                        body {
                            margin: 0;
                            height: 100vh;
                            display: flex;
                            justify-content: center;
                            align-items: center;
                            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                            background-color: #1a1a1a;
                            color: #ffffff;
                        }
                        h1 {
                            font-size: 4rem;
                            font-weight: 700;
                            letter-spacing: -0.05em;
                        }
                    </style>
                </head>
                <body>
                    <h1>codegen</h1>
                </body>
            </html>
            """

        @self.app.post("/slack/events")
        async def handle_slack_event(request: Request):
            """Handle incoming Slack events."""
            payload = await request.json()
            return self.slack.handle(payload)

        @self.app.post("/github/events")
        async def handle_github_event(request: Request):
            """Handle incoming GitHub events."""
            payload = await request.json()
            return self.github.handle(payload, request)

        @self.app.post("/linear/events")
        async def handle_linear_event(request: Request):
            """Handle incoming Linear events."""
            payload = await request.json()
            # Note: Linear handler needs to be implemented similar to others
            return {"message": "Linear event received"}

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the FastAPI application."""
        import uvicorn

        uvicorn.run(self.app, host=host, port=port, **kwargs)
