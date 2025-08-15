"""Main TUI application for Codegen CLI."""

import asyncio
import webbrowser

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import DataTable, Footer, Header, Static

from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id


class CodegenTUI(App):
    """Simple Codegen TUI for browsing agent runs."""

    CSS_PATH = "codegen_tui.tcss"
    TITLE = "Recent Agent Runs - Codegen CLI"
    BINDINGS = [
        Binding("escape,ctrl+c", "quit", "Quit", priority=True),
        Binding("enter", "open_url", "Open", show=True),
        Binding("r", "refresh", "Refresh", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.token = get_current_token()
        self.is_authenticated = bool(self.token)
        if self.is_authenticated:
            self.org_id = resolve_org_id()
        self.agent_runs = []

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        if not self.is_authenticated:
            yield Container(Static("⚠️  Not authenticated. Please run 'codegen login' first.", classes="warning-message"), id="auth-warning")
        else:
            with Vertical():
                yield Static("🤖 Your Recent API Agent Runs", classes="title")
                yield Static("Use ↑↓ to navigate, Enter to open, R to refresh, Esc to quit", classes="help")
                table = DataTable(id="agents-table", cursor_type="row")
                table.add_columns("Created", "Status", "Summary")
                yield table
        yield Footer()

    def on_mount(self) -> None:
        """Called when app starts."""
        if self.is_authenticated and self.org_id:
            task = asyncio.create_task(self._load_agents_data())
            # Store reference to prevent garbage collection
            self._load_task = task

    async def _load_agents_data(self) -> None:
        """Load agents data into the table."""
        table = self.query_one("#agents-table", DataTable)
        table.clear()

        if not self.token or not self.org_id:
            return

        try:
            import requests

            from codegen.cli.api.endpoints import API_ENDPOINT

            headers = {"Authorization": f"Bearer {self.token}"}

            # First get the current user ID
            user_response = requests.get(f"{API_ENDPOINT.rstrip('/')}/v1/users/me", headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            user_id = user_data.get("id")

            # Filter to only API source type and current user's agent runs
            params = {
                "source_type": "API",
                "limit": 20,  # Show recent 20
            }

            if user_id:
                params["user_id"] = user_id

            # Fetch agent runs
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/runs"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            response_data = response.json()

            agent_runs = response_data.get("items", [])
            self.agent_runs = agent_runs  # Store for URL opening

            for agent_run in agent_runs:
                run_id = str(agent_run.get("id", "Unknown"))
                status = agent_run.get("status", "Unknown")
                created_at = agent_run.get("created_at", "Unknown")

                # Use summary from API response (backend now handles extraction)
                summary = agent_run.get("summary", "") or "No summary"

                # Status with colored circles
                if status == "COMPLETE":
                    status_display = "● Complete"
                elif status == "ACTIVE":
                    status_display = "● Active"
                elif status == "RUNNING":
                    status_display = "● Running"
                elif status == "CANCELLED":
                    status_display = "● Cancelled"
                elif status == "ERROR":
                    status_display = "● Error"
                elif status == "FAILED":
                    status_display = "● Failed"
                elif status == "STOPPED":
                    status_display = "● Stopped"
                elif status == "PENDING":
                    status_display = "● Pending"
                else:
                    status_display = "● " + status

                # Format created date
                if created_at and created_at != "Unknown":
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                        created_display = dt.strftime("%m/%d %H:%M")
                    except (ValueError, TypeError):
                        created_display = created_at[:16] if len(created_at) > 16 else created_at
                else:
                    created_display = created_at

                # Truncate summary if too long
                summary_display = summary[:60] + "..." if summary and len(summary) > 60 else summary or "No summary"

                table.add_row(created_display, status_display, summary_display, key=run_id)

        except Exception as e:
            # If API call fails, show error in table
            table.add_row("Error", f"Failed to load: {e}", "")

    def action_open_url(self) -> None:
        """Open the selected agent run URL."""
        table = self.query_one("#agents-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.agent_runs):
            agent_run = self.agent_runs[table.cursor_row]
            run_id = agent_run.get("id")
            web_url = agent_run.get("web_url")

            if not web_url:
                # Construct URL if not provided
                web_url = f"https://codegen.com/traces/{run_id}"

            # Try to open URL
            try:
                webbrowser.open(web_url)
                self.notify(f"🌐 Opened {web_url}")
            except Exception as e:
                self.notify(f"❌ Failed to open URL: {e}", severity="error")

    def action_refresh(self) -> None:
        """Refresh agent runs data."""
        if self.is_authenticated and self.org_id:
            self.notify("🔄 Refreshing...", timeout=1)
            task = asyncio.create_task(self._load_agents_data())
            # Store reference to prevent garbage collection
            self._refresh_task = task
        else:
            self.notify("❌ Not authenticated or no org ID", severity="error")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui():
    """Run the Codegen TUI."""
    app = CodegenTUI()
    app.run()
