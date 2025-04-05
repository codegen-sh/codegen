import os
import sys
import logging
from typing import Dict, List, Any, Optional, Callable, Union

from agentgen.configs.models.codebase import CodebaseConfig
from agentgen.configs.models.secrets import SecretsConfig
from agentgen.sdk.core.codebase import Codebase
from agentgen.shared.logging.get_logger import get_logger

from .github import GitHub
from .slack import Slack

logger = get_logger(__name__)


class CodegenApp:
    """A FastAPI-based application for handling various code-related events."""

    github: GitHub
    slack: Slack

    def __init__(self, name: str, repo: Optional[str] = None, tmp_dir: str = "/tmp/codegen", commit: str | None = "latest"):
        self.name = name
        self.tmp_dir = tmp_dir

        # Create the FastAPI app
        self.app = FastAPI(title=name)

        # Initialize event handlers
        self.slack = Slack(self)
        self.github = GitHub(self)
        self.repo = repo
        self.commit = commit
        # Initialize codebase cache
        self.codebase: Codebase | None = None

        # Register routes
        self._setup_routes()

    def parse_repo(self) -> None:
        # Parse initial repos if provided
        if self.repo:
            self._parse_repo(self.repo, self.commit)

    def _parse_repo(self, repo_name: str, commit: str | None = None) -> None:
        """Parse a GitHub repository and cache it.

        Args:
            repo_name: Repository name in format "owner/repo"
        """
        try:
            logger.info(f"[CODEBASE] Parsing repository: {repo_name}")
            config = CodebaseConfig(sync_enabled=True)
            secrets = SecretsConfig(github_token=os.environ.get("GITHUB_ACCESS_TOKEN"))
            self.codebase = Codebase.from_repo(repo_full_name=repo_name, tmp_dir=self.tmp_dir, commit=commit, config=config, secrets=secrets)
            logger.info(f"[CODEBASE] Successfully parsed and cached: {repo_name}")
        except Exception as e:
            logger.exception(f"[CODEBASE] Failed to parse repository {repo_name}: {e!s}")
            raise

    def get_codebase(self) -> Codebase:
        """Get a cached codebase by repository name.

        Args:
            repo_name: Repository name in format "owner/repo"

        Returns:
            The cached Codebase instance

        Raises:
            KeyError: If the repository hasn't been parsed
        """
        if not self.codebase:
            msg = "Repository has not been parsed"
            raise KeyError(msg)
        return self.codebase

    def add_repo(self, repo_name: str) -> None:
        """Add a new repository to parse and cache.

        Args:
            repo_name: Repository name in format "owner/repo"
        """
        self._parse_repo(repo_name)

    async def simulate_event(self, provider: str, event_type: str, payload: dict) -> Any:
        """Simulate an event without running the server.

        Args:
            provider: The event provider ('slack' or 'github')
            event_type: The type of event to simulate
            payload: The event payload

        Returns:
            The handler's response
        """
        provider_map = {"slack": self.slack, "github": self.github}

        if provider not in provider_map:
            msg = f"Unknown provider: {provider}. Must be one of {list(provider_map.keys())}"
            raise ValueError(msg)

        handler = provider_map[provider]
        return await handler.handle(payload)

    async def root(self):
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

    async def handle_slack_event(self, request: Request):
        """Handle incoming Slack events."""
        payload = await request.json()
        return await self.slack.handle(payload)

    async def handle_github_event(self, request: Request):
        """Handle incoming GitHub events."""
        payload = await request.json()
        return await self.github.handle(payload, request)

    def _setup_routes(self):
        """Set up the FastAPI routes for different event types."""

        @self.app.get("/", response_class=HTMLResponse)
        async def _root():
            return await self.root()

        # @self.app.post("/{org}/{repo}/slack/events")
        @self.app.post("/slack/events")
        async def _handle_slack_event(request: Request):
            return await self.handle_slack_event(request)

        # @self.app.post("/{org}/{repo}/github/events")
        @self.app.post("/github/events")
        async def _handle_github_event(request: Request):
            return await self.handle_github_event(request)

    def run(self, host: str = "0.0.0.0", port: int = 8000, **kwargs):
        """Run the FastAPI application."""
        import uvicorn

        uvicorn.run(self.app, host=host, port=port, **kwargs)
