"""Main TUI application for Codegen CLI."""

import asyncio
import webbrowser

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import DataTable, Footer, Header, Static

from codegen.cli.auth.token_manager import get_current_token, get_cached_organizations, get_current_org_name, get_org_name_from_cache
from codegen.cli.utils.org import resolve_org_id


class CodegenTUI(App):
    """Simple Codegen TUI for browsing agent runs."""

    CSS_PATH = "codegen_theme.tcss"
    TITLE = "Codegen CLI"
    BINDINGS = [
        Binding("escape,ctrl+c", "quit", "Quit", priority=True),
        Binding("enter", "open_url", "Details", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("o", "select_org", "Org", show=True),
        Binding("p", "select_repo", "Repo", show=True),
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
                # Show current organization info - using id for updating
                org_name = get_current_org_name()
                org_display = f" ({org_name})" if org_name else f" (ID: {self.org_id})" if self.org_id else ""
                yield Static(f"🤖 Your Recent API Agent Runs{org_display}", classes="title", id="title-text")
                yield Static("Use ↑↓ to navigate, Enter for details, R to refresh, O for org, P for repo, Esc to quit", classes="help")
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
        
        # Ensure the table has focus for key events
        try:
            table = self.query_one("#agents-table", DataTable)
            table.focus()
        except Exception:
            # Table might not be ready yet, will focus after data loads
            pass

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
        
        # Ensure table has focus after data is loaded
        table.focus()

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle DataTable row selection (Enter key)."""
        if event.data_table.id == "agents-table":
            self.notify("🔍 Enter key pressed - opening agent details...", timeout=1)
            self.action_open_url()

    def action_open_url(self) -> None:
        """Open the selected agent run detail screen."""
        table = self.query_one("#agents-table", DataTable)
        if table.cursor_row is not None and table.cursor_row < len(self.agent_runs):
            agent_run = self.agent_runs[table.cursor_row]
            run_id = agent_run.get("id", "Unknown")
            
            self.notify(f"📱 Opening details for agent run {run_id}...", timeout=2)
            
            # Import here to avoid circular imports
            from codegen.cli.tui.agent_detail import AgentDetailTUI
            
            # Create and push the agent detail screen
            detail_screen = AgentDetailTUI(agent_run, self.org_id)
            self.push_screen(detail_screen)
        elif table.cursor_row is None:
            self.notify("❌ No row selected", severity="error", timeout=2)
        elif len(self.agent_runs) == 0:
            self.notify("❌ No agent runs available", severity="error", timeout=2)
        else:
            self.notify(f"❌ Invalid row selection: {table.cursor_row}/{len(self.agent_runs)}", severity="error", timeout=2)

    def action_refresh(self) -> None:
        """Refresh agent runs data."""
        if self.is_authenticated:
            # Refresh org ID and title
            old_org_id = self.org_id
            self.org_id = resolve_org_id()
            self._refresh_title()
            
            if self.org_id:
                self.notify("🔄 Refreshing...", timeout=1)
                task = asyncio.create_task(self._load_agents_data())
                # Store reference to prevent garbage collection
                self._refresh_task = task
            else:
                self.notify("❌ No organization configured", severity="error")
        else:
            self.notify("❌ Not authenticated", severity="error")

    def action_select_org(self) -> None:
        """Launch the organization selector TUI."""
        if not self.is_authenticated:
            self.notify("❌ Not authenticated. Please login first.", severity="error")
            return

        # Check if organizations are available in cache
        cached_orgs = get_cached_organizations()
        if not cached_orgs:
            self.notify("❌ No organizations found. Please run 'codegen login' to refresh.", severity="error")
            return

        try:
            # Import here to avoid circular imports
            from codegen.cli.commands.org.tui import OrgSelectorTUI
            
            # Launch the organization selector as a sub-screen
            def on_org_selected():
                # Debug callback trigger
                self.notify("🔧 Org selector callback triggered!", timeout=0.5)
                
                # Refresh the org_id and reload data when org selector closes
                old_org_id = self.org_id
                self.org_id = resolve_org_id()
                
                # Debug org ID change
                self.notify(f"🔧 Org ID: {old_org_id} → {self.org_id}", timeout=1)
                
                # Refresh the title to show new organization
                self._refresh_title()
                
                if self.org_id and self.org_id != old_org_id:
                    self.notify("🔄 Refreshing data for new organization...", timeout=1)
                    task = asyncio.create_task(self._load_agents_data())
                    self._refresh_task = task
                elif not self.org_id:
                    self.notify("❌ No organization configured", severity="error")
                else:
                    self.notify("ℹ  Organization unchanged", timeout=1)
            
            org_selector = OrgSelectorTUI()
            # Set up a callback when the screen is dismissed
            self.push_screen(org_selector, callback=lambda _: on_org_selected())
        except Exception as e:
            self.notify(f"❌ Failed to launch org selector: {e}", severity="error")

    def action_select_repo(self) -> None:
        """Launch the repository selector TUI."""
        if not self.is_authenticated:
            self.notify("❌ Not authenticated. Please login first.", severity="error")
            return

        try:
            # Import here to avoid circular imports
            from codegen.cli.commands.repo.tui import RepoSelectorTUI
            
            # Launch the repository selector as a sub-screen
            def on_repo_selected():
                # Debug callback trigger
                self.notify("🔧 Repo selector callback triggered!", timeout=0.5)
                
                # Notify user about repo change (repos don't affect agent runs directly in this TUI)
                self.notify("✅ Repository configuration updated!", timeout=2)
            
            repo_selector = RepoSelectorTUI()
            # Set up a callback when the screen is dismissed
            self.push_screen(repo_selector, callback=lambda _: on_repo_selected())
        except Exception as e:
            self.notify(f"❌ Failed to launch repo selector: {e}", severity="error")

    def _refresh_title(self) -> None:
        """Refresh the title to show current organization."""
        try:
            if self.is_authenticated:
                title_widget = self.query_one("#title-text", Static)
                
                # Try to get org name from cache first (more reliable after org change)
                org_name = None
                if self.org_id:
                    org_name = get_org_name_from_cache(self.org_id)
                
                # Fallback to stored org name
                if not org_name:
                    org_name = get_current_org_name()
                
                org_display = f" ({org_name})" if org_name else f" (ID: {self.org_id})" if self.org_id else ""
                new_title = f"🤖 Your Recent API Agent Runs{org_display}"
                title_widget.update(new_title)
                
                # Debug notification
                self.notify(f"🔧 Title updated: {new_title}", timeout=0.5)
        except Exception as e:
            # Debug any errors
            self.notify(f"❌ Error updating title: {e}", severity="error", timeout=1)

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui():
    """Run the Codegen TUI."""
    app = CodegenTUI()
    app.run()
