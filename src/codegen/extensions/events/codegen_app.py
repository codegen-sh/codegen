from typing import Any, Optional

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

from codegen.sdk.core.codebase import Codebase
from codegen.shared.logging.get_logger import get_logger

from .github import GitHub
from .linear import Linear
from .slack import Slack

logger = get_logger(__name__)


class CodegenApp:
    """A FastAPI-based application for handling various code-related events."""

    github: GitHub
    linear: Linear
    slack: Slack

    def __init__(self, name: str, repos: Optional[list[str]] = None, modal_api_key: Optional[str] = None, tmp_dir: str = "/tmp/codegen"):
        self.name = name
        self._modal_api_key = modal_api_key
        self.tmp_dir = tmp_dir

        # Create the FastAPI app
        self.app = FastAPI(title=name)

        # Initialize event handlers
        self.linear = Linear(self)
        self.slack = Slack(self)
        self.github = GitHub(self)

        # Initialize codebase cache
        self.codebases: dict[str, Codebase] = {}

        # Parse initial repos if provided
        if repos:
            for repo in repos:
                self._parse_repo(repo)

        # Register routes
        self._setup_routes()

    def _parse_repo(self, repo_name: str) -> None:
        """Parse a GitHub repository and cache it.

        Args:
            repo_name: Repository name in format "owner/repo"
        """
        try:
            logger.info(f"[CODEBASE] Parsing repository: {repo_name}")
            self.codebases[repo_name] = Codebase.from_repo(repo_name, tmp_dir=self.tmp_dir)
            logger.info(f"[CODEBASE] Successfully parsed and cached: {repo_name}")
        except Exception as e:
            logger.exception(f"[CODEBASE] Failed to parse repository {repo_name}: {e!s}")
            raise

    def get_codebase(self, repo_name: str) -> Codebase:
        """Get a cached codebase by repository name.

        Args:
            repo_name: Repository name in format "owner/repo"

        Returns:
            The cached Codebase instance

        Raises:
            KeyError: If the repository hasn't been parsed
        """
        if repo_name not in self.codebases:
            msg = f"Repository {repo_name} has not been parsed. Available repos: {list(self.codebases.keys())}"
            raise KeyError(msg)
        return self.codebases[repo_name]

    def add_repo(self, repo_name: str) -> None:
        """Add a new repository to parse and cache.

        Args:
            repo_name: Repository name in format "owner/repo"
        """
        self._parse_repo(repo_name)

    async def simulate_event(self, provider: str, event_type: str, payload: dict) -> Any:
        """Simulate an event without running the server.

        Args:
            provider: The event provider ('slack', 'github', or 'linear')
            event_type: The type of event to simulate
            payload: The event payload

        Returns:
            The handler's response
        """
        provider_map = {"slack": self.slack, "github": self.github, "linear": self.linear}

        if provider not in provider_map:
            msg = f"Unknown provider: {provider}. Must be one of {list(provider_map.keys())}"
            raise ValueError(msg)

        handler = provider_map[provider]
        return await handler.handle(payload)

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
            return await self.slack.handle(payload)

        @self.app.post("/github/events")
        async def handle_github_event(request: Request):
            """Handle incoming GitHub events."""
            payload = await request.json()
            return await self.github.handle(payload, request)

        @self.app.post("/linear/events")
        async def handle_linear_event(request: Request):
            """Handle incoming Linear events."""
            payload = await request.json()
            return await self.linear.handle(payload)

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the FastAPI application."""
        import uvicorn

        uvicorn.run(self.app, host=host, port=port, **kwargs)
