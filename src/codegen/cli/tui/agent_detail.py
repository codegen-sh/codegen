"""Agent Detail TUI screen for viewing individual agent runs."""

import asyncio
import json
from pathlib import Path
from typing import Any

import requests
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Static

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id
from codegen.git.repo_operator.local_git_repo import LocalGitRepo


class AgentDetailTUI(Screen):
    """TUI screen for viewing agent run details and performing actions."""

    CSS_PATH = "codegen_theme.tcss"
    BINDINGS = [
        Binding("escape,q", "back", "Back", show=True),
        Binding("j", "view_json", "View JSON", show=True),
        Binding("p", "pull_branch", "Pull Branch", show=True),
        Binding("w", "open_web", "Open Web", show=True),
    ]

    def __init__(self, agent_run: dict[str, Any], org_id: int | None = None):
        super().__init__()
        self.agent_run = agent_run
        self.org_id = org_id or resolve_org_id()
        self.agent_data: dict[str, Any] | None = None
        self.is_loading = False

    def compose(self) -> ComposeResult:
        """Create child widgets for the agent detail screen."""
        run_id = self.agent_run.get("id", "Unknown")
        summary = self.agent_run.get("summary", "No summary available")

        yield Header()

        with Vertical():
            yield Static(f"🤖 Agent Run Details - ID: {run_id}", classes="title", id="detail-title")
            yield Static("Use J for JSON, P to pull branch, W for web, Q/Esc to go back", classes="help")

            # Basic info section
            info_table = DataTable(id="info-table", cursor_type="none")
            info_table.add_columns("Property", "Value")
            yield info_table

            # Actions section
            with Horizontal(id="actions-section"):
                yield Button("📄 View JSON", id="json-btn", variant="primary")
                yield Button("🔀 Pull Branch", id="pull-btn", variant="default")
                yield Button("🌐 Open Web", id="web-btn", variant="default")
                yield Button("⬅️ Back", id="back-btn", variant="default")

            # Status/loading area
            yield Static("", id="status-text")

        yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        self._populate_basic_info()
        # Load detailed data in background
        task = asyncio.create_task(self._load_detailed_data())
        self._load_task = task

    def _populate_basic_info(self) -> None:
        """Populate the info table with basic agent run information."""
        info_table = self.query_one("#info-table", DataTable)

        # Basic info from the agent run data
        run_id = self.agent_run.get("id", "Unknown")
        status = self.agent_run.get("status", "Unknown")
        created_at = self.agent_run.get("created_at", "Unknown")
        summary = self.agent_run.get("summary", "No summary available")
        web_url = self.agent_run.get("web_url", "Not available")

        # Format status with emoji
        status_display = status
        if status == "COMPLETE":
            status_display = "✅ Complete"
        elif status == "RUNNING":
            status_display = "🏃 Running"
        elif status == "FAILED":
            status_display = "❌ Failed"
        elif status == "STOPPED":
            status_display = "⏹️ Stopped"
        elif status == "PENDING":
            status_display = "⏳ Pending"

        # Add rows to info table
        info_table.add_row("ID", str(run_id))
        info_table.add_row("Status", status_display)
        info_table.add_row("Created", created_at)
        info_table.add_row("Summary", summary)
        info_table.add_row("Web URL", web_url)

    async def _load_detailed_data(self) -> None:
        """Load detailed agent run data from the API."""
        if self.is_loading:
            return

        self.is_loading = True
        status_text = self.query_one("#status-text", Static)
        status_text.update("🔄 Loading detailed agent data...")

        try:
            token = get_current_token()
            if not token:
                status_text.update("❌ Not authenticated")
                return

            run_id = self.agent_run.get("id")
            if not run_id:
                status_text.update("❌ No agent run ID available")
                return

            headers = {"Authorization": f"Bearer {token}"}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/run/{run_id}"

            response = requests.get(url, headers=headers)
            response.raise_for_status()
            self.agent_data = response.json()

            # Update info table with additional details
            self._update_info_with_detailed_data()
            status_text.update("✅ Agent data loaded successfully")

        except requests.HTTPError as e:
            if e.response.status_code == 404:
                status_text.update(f"❌ Agent run {run_id} not found")
            elif e.response.status_code == 403:
                status_text.update(f"❌ Access denied to agent run {run_id}")
            else:
                status_text.update(f"❌ HTTP {e.response.status_code}: {e}")
        except Exception as e:
            status_text.update(f"❌ Error loading data: {e}")
        finally:
            self.is_loading = False

    def _update_info_with_detailed_data(self) -> None:
        """Update the info table with detailed data from the API."""
        if not self.agent_data:
            return

        info_table = self.query_one("#info-table", DataTable)

        # Check for GitHub PRs
        github_prs = self.agent_data.get("github_pull_requests", [])
        if github_prs:
            pr_info = f"{len(github_prs)} PR(s) available"
            for i, pr in enumerate(github_prs[:3]):  # Show up to 3 PRs
                branch = pr.get("head", {}).get("ref", "unknown")
                pr_info += f"\n  • {branch}"
            if len(github_prs) > 3:
                pr_info += f"\n  • ... and {len(github_prs) - 3} more"
        else:
            pr_info = "No PRs available"

        info_table.add_row("PR Branches", pr_info)

        # Add model info if available
        model = self.agent_data.get("model", "Unknown")
        info_table.add_row("Model", model)

    # Action handlers
    def action_back(self) -> None:
        """Go back to the main screen."""
        self.app.pop_screen()

    def action_view_json(self) -> None:
        """View the full JSON data for the agent run."""
        if not self.agent_data:
            self.notify("❌ Detailed data not loaded yet", severity="error")
            return

        # Create a JSON viewer screen
        json_screen = JSONViewerTUI(self.agent_data)
        self.app.push_screen(json_screen)

    def action_pull_branch(self) -> None:
        """Pull the PR branch for this agent run."""
        if not self.agent_data:
            self.notify("❌ Detailed data not loaded yet", severity="error")
            return

        # Check if we're in a git repository
        try:
            current_repo = LocalGitRepo(Path.cwd())
            if not current_repo.has_remote():
                self.notify("❌ Not in a git repository with remotes", severity="error")
                return
        except Exception:
            self.notify("❌ Not in a valid git repository", severity="error")
            return

        # Check for GitHub PRs
        github_prs = self.agent_data.get("github_pull_requests", [])
        if not github_prs:
            self.notify("❌ No PR branches available for this agent run", severity="error")
            return

        # For now, take the first PR - in the future we could show a selector
        pr = github_prs[0]
        branch_name = pr.get("head", {}).get("ref")
        repo_clone_url = pr.get("head", {}).get("repo", {}).get("clone_url")

        if not branch_name or not repo_clone_url:
            self.notify("❌ Invalid PR data", severity="error")
            return

        # Start the pull process
        task = asyncio.create_task(self._pull_branch_async(branch_name, repo_clone_url))
        self._pull_task = task

    async def _pull_branch_async(self, branch_name: str, repo_clone_url: str) -> None:
        """Asynchronously pull the PR branch."""
        status_text = self.query_one("#status-text", Static)
        status_text.update(f"🔄 Pulling branch {branch_name}...")

        try:
            current_repo = LocalGitRepo(Path.cwd())

            # Add remote if it doesn't exist
            remote_name = "codegen-pr"
            try:
                current_repo.add_remote(remote_name, repo_clone_url)
            except Exception:
                # Remote might already exist
                pass

            # Fetch and checkout the branch
            current_repo.fetch_remote(remote_name)
            current_repo.checkout_branch(f"{remote_name}/{branch_name}", branch_name)

            status_text.update(f"✅ Successfully checked out branch: {branch_name}")
            self.notify(f"✅ Switched to branch: {branch_name}")

        except Exception as e:
            error_msg = f"❌ Failed to pull branch: {e}"
            status_text.update(error_msg)
            self.notify(error_msg, severity="error")

    def action_open_web(self) -> None:
        """Open the agent run in the web browser."""
        web_url = self.agent_run.get("web_url")
        if not web_url:
            run_id = self.agent_run.get("id")
            web_url = f"https://codegen.com/traces/{run_id}"

        try:
            import webbrowser

            webbrowser.open(web_url)
            self.notify(f"🌐 Opened {web_url}")
        except Exception as e:
            self.notify(f"❌ Failed to open URL: {e}", severity="error")

    # Button event handlers
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "json-btn":
            self.action_view_json()
        elif event.button.id == "pull-btn":
            self.action_pull_branch()
        elif event.button.id == "web-btn":
            self.action_open_web()
        elif event.button.id == "back-btn":
            self.action_back()


class JSONViewerTUI(Screen):
    """TUI screen for viewing JSON data."""

    CSS_PATH = "codegen_theme.tcss"
    BINDINGS = [
        Binding("escape,q", "back", "Back", show=True),
    ]

    def __init__(self, data: dict[str, Any]):
        super().__init__()
        self.data = data

    def compose(self) -> ComposeResult:
        """Create child widgets for the JSON viewer."""
        yield Header()

        with Vertical():
            yield Static("📄 Agent Run JSON Data", classes="title")
            yield Static("Use Q/Esc to go back", classes="help")

            # Format JSON with pretty printing
            try:
                json_text = json.dumps(self.data, indent=2, sort_keys=True)
                yield Static(json_text, id="json-content")
            except Exception as e:
                yield Static(f"Error formatting JSON: {e}", id="json-content")

        yield Footer()

    def action_back(self) -> None:
        """Go back to the agent detail screen."""
        self.app.pop_screen()
