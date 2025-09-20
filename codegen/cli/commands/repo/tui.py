"""Repository selector TUI using Textual."""

import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from codegen.cli.auth.token_manager import get_cached_repositories, get_current_token
from codegen.cli.utils.repo import (
    get_current_repo_id, 
    set_repo_env_variable,
    update_env_file_with_repo,
    ensure_repositories_cached
)
from codegen.cli.utils.org import resolve_org_id


class RepoSelectorTUI(Screen):
    """TUI for selecting and switching repositories."""

    BINDINGS = [
        Binding("escape,ctrl+c", "quit", "Quit", priority=True),
        Binding("enter", "select_repo", "Select", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.repositories = ensure_repositories_cached() or []
        self.current_repo_id = get_current_repo_id()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        if not self.repositories:
            yield Container(
                Static("⚠️  No repositories found. Fetching repositories...", classes="warning-message"), 
                id="no-repos-warning"
            )
        else:
            with Vertical():
                yield Static("🗂️ Select Your Repository", classes="title")
                yield Static("Use ↑↓ to navigate, Enter to select, Q/Esc to quit", classes="help")
                
                table = DataTable(id="repos-table", cursor_type="row")
                table.add_columns("Current", "ID", "Repository Name")
                
                # Get the actual current repo ID (checks environment variables first)
                actual_current_repo_id = get_current_repo_id()
                
                for repo in self.repositories:
                    repo_id = repo["id"]
                    repo_name = repo["name"]
                    is_current = "●" if repo_id == actual_current_repo_id else " "
                    
                    table.add_row(is_current, str(repo_id), repo_name, key=str(repo_id))
                
                yield table
                
                yield Static(
                    "\n💡 Selecting a repository will update your CODEGEN_REPO_ID environment variable.", 
                    classes="help"
                )
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        if self.repositories:
            try:
                table = self.query_one("#repos-table", DataTable)
                table.focus()
            except Exception:
                pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle DataTable row selection (Enter key)."""
        if event.data_table.id == "repos-table":
            self._handle_repo_selection()

    def action_select_repo(self) -> None:
        """Select repository (fallback for direct key binding)."""
        self._handle_repo_selection()

    def _handle_repo_selection(self) -> None:
        """Handle repository selection logic."""
        try:
            table = self.query_one("#repos-table", DataTable)
            if table.cursor_row is not None and table.cursor_row < len(self.repositories):
                selected_repo = self.repositories[table.cursor_row]
                repo_id = selected_repo["id"]
                repo_name = selected_repo["name"]
                
                self._set_repository(repo_id, repo_name)
        except Exception as e:
            self.notify(f"❌ Error selecting repository: {e}", severity="error")

    def _set_repository(self, repo_id: int, repo_name: str) -> None:
        """Set the selected repository as the current one."""
        # Update environment variable
        os.environ["CODEGEN_REPO_ID"] = str(repo_id)
        
        # Try to update .env file
        env_updated = self._update_env_file(repo_id)
        
        if env_updated:
            self.notify(f"✓ Set default repository: {repo_name} (ID: {repo_id})")
            self.notify("✓ Updated .env file with CODEGEN_REPO_ID")
        else:
            self.notify(f"✓ Set repository: {repo_name} (ID: {repo_id})")
            self.notify("ℹ  Add 'export CODEGEN_REPO_ID={repo_id}' to your shell for persistence")
        
        # Wait a moment for user to see the notifications, then exit
        self.set_timer(2.0, self._close_screen)

    def _update_env_file(self, repo_id: int) -> bool:
        """Update the .env file with the new repository ID."""
        env_file_path = ".env"
        
        try:
            lines = []
            key_updated = False
            key_to_update = "CODEGEN_REPO_ID"
            
            # Read existing .env file if it exists
            if os.path.exists(env_file_path):
                with open(env_file_path, "r") as f:
                    lines = f.readlines()
            
            # Update or add the key
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key_to_update}="):
                    lines[i] = f"{key_to_update}={repo_id}\n"
                    key_updated = True
                    break
            
            # If key wasn't found, add it
            if not key_updated:
                if lines and not lines[-1].endswith('\n'):
                    lines.append('\n')
                lines.append(f"{key_to_update}={repo_id}\n")
            
            # Write back to file
            with open(env_file_path, "w") as f:
                f.writelines(lines)
            
            return True
            
        except Exception:
            return False

    def _close_screen(self) -> None:
        """Close the screen."""
        if hasattr(self.app, 'pop_screen'):
            self.app.pop_screen()
        else:
            self.app.exit()

    def action_quit(self) -> None:
        """Quit the TUI."""
        self._close_screen()


class RepoSelectorApp(App):
    """Standalone app wrapper for the repository selector."""
    
    CSS_PATH = "../../tui/codegen_theme.tcss"  # Use custom Codegen theme
    TITLE = "Repository Selector - Codegen CLI"
    BINDINGS = [
        Binding("escape,ctrl+c", "quit", "Quit", priority=True),
        Binding("enter", "select_repo", "Select", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.repositories = ensure_repositories_cached() or []
        self.current_repo_id = get_current_repo_id()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        if not self.repositories:
            yield Container(
                Static("⚠️  No repositories found. Fetching repositories...", classes="warning-message"), 
                id="no-repos-warning"
            )
        else:
            with Vertical():
                yield Static("🗂️ Select Your Repository", classes="title")
                yield Static("Use ↑↓ to navigate, Enter to select, Q/Esc to quit", classes="help")
                
                table = DataTable(id="repos-table", cursor_type="row")
                table.add_columns("Current", "ID", "Repository Name")
                
                # Get the actual current repo ID (checks environment variables first)
                actual_current_repo_id = get_current_repo_id()
                
                for repo in self.repositories:
                    repo_id = repo["id"]
                    repo_name = repo["name"]
                    is_current = "●" if repo_id == actual_current_repo_id else " "
                    
                    table.add_row(is_current, str(repo_id), repo_name, key=str(repo_id))
                
                yield table
                
                yield Static(
                    "\n💡 Selecting a repository will update your CODEGEN_REPO_ID environment variable.", 
                    classes="help"
                )
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app starts."""
        if self.repositories:
            try:
                table = self.query_one("#repos-table", DataTable)
                table.focus()
            except Exception:
                pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle DataTable row selection (Enter key)."""
        if event.data_table.id == "repos-table":
            self._handle_repo_selection()

    def action_select_repo(self) -> None:
        """Select repository (fallback for direct key binding)."""
        self._handle_repo_selection()

    def _handle_repo_selection(self) -> None:
        """Handle repository selection logic."""
        try:
            table = self.query_one("#repos-table", DataTable)
            if table.cursor_row is not None and table.cursor_row < len(self.repositories):
                selected_repo = self.repositories[table.cursor_row]
                repo_id = selected_repo["id"]
                repo_name = selected_repo["name"]
                
                self._set_repository(repo_id, repo_name)
        except Exception as e:
            self.notify(f"❌ Error selecting repository: {e}", severity="error")

    def _set_repository(self, repo_id: int, repo_name: str) -> None:
        """Set the selected repository as the current one."""
        # Update environment variable
        os.environ["CODEGEN_REPO_ID"] = str(repo_id)
        
        # Try to update .env file
        env_updated = self._update_env_file(repo_id)
        
        if env_updated:
            self.notify(f"✓ Set default repository: {repo_name} (ID: {repo_id})")
            self.notify("✓ Updated .env file with CODEGEN_REPO_ID")
        else:
            self.notify(f"✓ Set repository: {repo_name} (ID: {repo_id})")
            self.notify("ℹ  Add 'export CODEGEN_REPO_ID={repo_id}' to your shell for persistence")
        
        # Wait a moment for user to see the notifications, then exit
        self.set_timer(2.0, self.exit)

    def _update_env_file(self, repo_id: int) -> bool:
        """Update the .env file with the new repository ID."""
        env_file_path = ".env"
        
        try:
            lines = []
            key_updated = False
            key_to_update = "CODEGEN_REPO_ID"
            
            # Read existing .env file if it exists
            if os.path.exists(env_file_path):
                with open(env_file_path, "r") as f:
                    lines = f.readlines()
            
            # Update or add the key
            for i, line in enumerate(lines):
                if line.strip().startswith(f"{key_to_update}="):
                    lines[i] = f"{key_to_update}={repo_id}\n"
                    key_updated = True
                    break
            
            # If key wasn't found, add it
            if not key_updated:
                if lines and not lines[-1].endswith('\n'):
                    lines.append('\n')
                lines.append(f"{key_to_update}={repo_id}\n")
            
            # Write back to file
            with open(env_file_path, "w") as f:
                f.writelines(lines)
            
            return True
            
        except Exception:
            return False