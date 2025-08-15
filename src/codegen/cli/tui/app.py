"""Main TUI application for Codegen CLI."""

import asyncio
from datetime import UTC, datetime

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.widgets import DataTable, Footer, Header, Static, TabbedContent, TabPane

from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id


class CodegenTUI(App):
    """Main Codegen TUI Application."""

    TITLE = "Codegen CLI"
    CSS_PATH = "codegen_tui.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("ctrl+c", "quit", "Quit"),
    ]

    # Reactive attributes
    org_id: reactive[int | None] = reactive(None)
    is_authenticated: reactive[bool] = reactive(False)

    def __init__(self):
        super().__init__()
        self.token = get_current_token()
        self.is_authenticated = bool(self.token)
        if self.is_authenticated:
            self.org_id = resolve_org_id()

    def compose(self) -> ComposeResult:
        """Compose the main UI."""
        yield Header()

        if not self.is_authenticated:
            yield Container(Static("⚠️  Not authenticated. Please run 'codegen login' first.", classes="warning-message"), id="auth-warning")
        else:
            with TabbedContent(initial="dashboard"):
                with TabPane("Dashboard", id="dashboard"):
                    yield from self._compose_dashboard()

                with TabPane("Agents", id="agents"):
                    yield from self._compose_agents()

                with TabPane("Integrations", id="integrations"):
                    yield from self._compose_integrations()

                with TabPane("Tools", id="tools"):
                    yield from self._compose_tools()

        yield Footer()

    def _compose_dashboard(self) -> ComposeResult:
        """Compose the dashboard tab."""
        with Vertical():
            yield Static("📊 Dashboard", classes="tab-title")
            with Horizontal():
                yield Static("🏢 Organization:", classes="info-label")
                yield Static(str(self.org_id) if self.org_id else "Unknown", classes="info-value")
            with Horizontal():
                yield Static("🕐 Last Updated:", classes="info-label")
                yield Static(datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"), classes="info-value")
            yield Static("🤖 Recent API Agent Runs", classes="tab-title")
            dashboard_table = DataTable(id="dashboard-agents-table")
            dashboard_table.add_columns("Created", "Status", "Summary", "Link")
            yield dashboard_table

    def _compose_agents(self) -> ComposeResult:
        """Compose the agents tab."""
        with Vertical():
            yield Static("🤖 Your Recent API Agent Runs", classes="tab-title")
            table = DataTable(id="agents-table")
            table.add_columns("Created", "Status", "Summary", "Link")
            yield table

    def _compose_integrations(self) -> ComposeResult:
        """Compose the integrations tab."""
        with Vertical():
            yield Static("🔌 Integrations", classes="tab-title")
            table = DataTable(id="integrations-table")
            table.add_columns("Integration", "Status", "Type", "Details")
            yield table

    def _compose_tools(self) -> ComposeResult:
        """Compose the tools tab."""
        with Vertical():
            yield Static("🛠️ Tools", classes="tab-title")
            table = DataTable(id="tools-table")
            table.add_columns("Tool Name", "Description", "Category")
            yield table

    async def on_mount(self) -> None:
        """Initialize the app on mount."""
        if self.is_authenticated:
            if self.org_id is None:
                self.notify("⚠️ No organization ID found. Set CODEGEN_ORG_ID or REPOSITORY_ORG_ID.", severity="warning")
            else:
                # Load initial data
                await self._load_all_data()

    async def _load_all_data(self) -> None:
        """Load data for all tabs."""
        if not self.is_authenticated or not self.org_id:
            return

        try:
            # Load data in parallel
            await asyncio.gather(self._load_dashboard_data(), self._load_agents_data(), self._load_integrations_data(), self._load_tools_data(), return_exceptions=True)
        except Exception as e:
            self.notify(f"Error loading data: {e}", severity="error")

    async def _load_dashboard_data(self) -> None:
        """Load dashboard data (recent agent runs summary)."""
        table = self.query_one("#dashboard-agents-table", DataTable)
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

            # Filter to only API source type and current user's agent runs, limit to 5 for dashboard
            params = {
                "source_type": "API",
                "limit": 5,  # Show only top 5 recent
            }

            if user_id:
                params["user_id"] = user_id

            # Fetch agent runs
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/runs"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            response_data = response.json()

            agent_runs = response_data.get("items", [])

            for agent_run in agent_runs:
                run_id = str(agent_run.get("id", "Unknown"))
                status = agent_run.get("status", "Unknown")
                created_at = agent_run.get("created_at", "Unknown")

                # Extract summary from task_timeline_json, similar to frontend
                timeline = agent_run.get("task_timeline_json")
                summary = None
                if timeline and isinstance(timeline, dict) and "summary" in timeline:
                    if isinstance(timeline["summary"], str):
                        summary = timeline["summary"]

                # Fall back to goal_prompt if no summary
                if not summary:
                    summary = agent_run.get("goal_prompt", "")

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

                # Truncate summary if too long for dashboard
                summary_display = summary[:40] + "..." if summary and len(summary) > 40 else summary or "No summary"

                # Create web link for the agent run
                web_url = agent_run.get("web_url")
                if not web_url:
                    # Construct URL if not provided
                    web_url = f"https://codegen.com/traces/{run_id}"
                link_display = web_url

                table.add_row(created_display, status_display, summary_display, link_display)

        except Exception as e:
            # If API call fails, show error in table
            table.add_row("Error", f"Failed to load: {e}", "", "")

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
                "limit": 10,  # Show recent 10
            }

            if user_id:
                params["user_id"] = user_id

            # Fetch agent runs
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/runs"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            response_data = response.json()

            agent_runs = response_data.get("items", [])

            for agent_run in agent_runs:
                run_id = str(agent_run.get("id", "Unknown"))
                status = agent_run.get("status", "Unknown")
                source_type = agent_run.get("source_type", "Unknown")
                created_at = agent_run.get("created_at", "Unknown")

                # Extract summary from task_timeline_json, similar to frontend
                timeline = agent_run.get("task_timeline_json")
                summary = None
                if timeline and isinstance(timeline, dict) and "summary" in timeline:
                    if isinstance(timeline["summary"], str):
                        summary = timeline["summary"]

                # Fall back to goal_prompt if no summary
                if not summary:
                    summary = agent_run.get("goal_prompt", "")

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
                summary_display = summary[:30] + "..." if summary and len(summary) > 30 else summary or "No summary"

                # Create web link for the agent run
                web_url = agent_run.get("web_url")
                if not web_url:
                    # Construct URL if not provided
                    web_url = f"https://codegen.com/traces/{run_id}"
                link_display = web_url

                table.add_row(created_display, status_display, summary_display, link_display)

        except Exception as e:
            # If API call fails, show error in table
            table.add_row("Error", f"Failed to load: {e}", "", "")

    async def _load_integrations_data(self) -> None:
        """Load integrations data into the table."""
        table = self.query_one("#integrations-table", DataTable)
        table.clear()

        # TODO: Implement actual API call
        # For now, add placeholder data
        table.add_row("GitHub", "✅ Active", "App Install", "Install ID: 12345")
        table.add_row("Slack", "✅ Active", "User Token", "Token ID: 67890")
        table.add_row("Linear", "❌ Inactive", "User Token", "No token")

    async def _load_tools_data(self) -> None:
        """Load tools data into the table."""
        table = self.query_one("#tools-table", DataTable)
        table.clear()

        # TODO: Implement actual API call
        # For now, add placeholder data
        table.add_row("github_create_pr", "Create a pull request on GitHub", "GitHub")
        table.add_row("run_command", "Execute a shell command", "System")
        table.add_row("file_write", "Write content to a file", "File System")

    def action_refresh(self) -> None:
        """Refresh all data."""
        if self.is_authenticated and self.org_id:
            self.notify("🔄 Refreshing data...", timeout=1)
            task = asyncio.create_task(self._load_all_data())
            # Store reference to prevent garbage collection
            self._refresh_task = task
        else:
            self.notify("❌ Not authenticated or no org ID", severity="error")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui() -> None:
    """Run the Codegen TUI application."""
    app = CodegenTUI()
    app.run()


if __name__ == "__main__":
    run_tui()
