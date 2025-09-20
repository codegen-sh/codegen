"""Organization selector TUI using Textual - Fixed version."""

import os

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Footer, Header, Static

from codegen.cli.auth.token_manager import get_cached_organizations, get_current_org_id
from codegen.cli.utils.org import resolve_org_id


class OrgSelectorTUI(Screen):
    """TUI for selecting and switching organizations."""

    BINDINGS = [
        Binding("escape,ctrl+c", "quit", "Quit", priority=True),
        Binding("enter", "select_org", "Select", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.organizations = get_cached_organizations() or []
        self.current_org_id = get_current_org_id()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        if not self.organizations:
            yield Container(
                Static("⚠️  No organizations found. Please run 'codegen login' first.", classes="warning-message"), 
                id="no-orgs-warning"
            )
        else:
            with Vertical():
                yield Static("🏢 Select Your Organization", classes="title")
                yield Static("Use ↑↓ to navigate, Enter to select, Q/Esc to quit", classes="help")
                
                table = DataTable(id="orgs-table", cursor_type="row")
                table.add_columns("Current", "ID", "Organization Name")
                
                # Get the actual current org ID (checks environment variables first)
                actual_current_org_id = resolve_org_id()
                
                for org in self.organizations:
                    org_id = org["id"]
                    org_name = org["name"]
                    is_current = "●" if org_id == actual_current_org_id else " "
                    
                    table.add_row(is_current, str(org_id), org_name, key=str(org_id))
                
                yield table
                
                yield Static(
                    "\n💡 Selecting an organization will update your CODEGEN_ORG_ID environment variable.", 
                    classes="help"
                )
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when the screen is mounted."""
        # Set focus on the table if it exists
        if self.organizations:
            try:
                table = self.query_one("#orgs-table", DataTable)
                table.focus()
            except Exception:
                pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle DataTable row selection (Enter key)."""
        if event.data_table.id == "orgs-table":
            self._handle_org_selection()

    def action_select_org(self) -> None:
        """Select the highlighted organization (fallback action)."""
        self._handle_org_selection()

    def _handle_org_selection(self) -> None:
        """Handle organization selection logic."""
        if not self.organizations:
            self.notify("❌ No organizations available", severity="error")
            return

        try:
            table = self.query_one("#orgs-table", DataTable)
            
            if table.cursor_row is not None and table.cursor_row < len(self.organizations):
                # Get the selected organization directly from the cursor position
                selected_org = self.organizations[table.cursor_row]
                selected_org_id = selected_org["id"]

                # Set the organization
                self._set_organization(selected_org_id, selected_org["name"])
            else:
                self.notify(f"❌ Invalid cursor position: {table.cursor_row}/{len(self.organizations)}", severity="error")
        except Exception as e:
            self.notify(f"❌ Error in select org: {e}", severity="error")

    def _set_organization(self, org_id: int, org_name: str) -> None:
        """Set the selected organization as default."""
        # Set environment variable
        os.environ["CODEGEN_ORG_ID"] = str(org_id)
        
        # Try to update .env file
        env_updated = self._update_env_file(org_id)
        
        if env_updated:
            self.notify(f"✓ Set default organization: {org_name} (ID: {org_id})")
            self.notify("✓ Updated .env file with CODEGEN_ORG_ID")
        else:
            self.notify(f"✓ Set organization: {org_name} (ID: {org_id})")
            self.notify("ℹ  Add 'export CODEGEN_ORG_ID={org_id}' to your shell for persistence")
        
        # Wait a moment for user to see the notifications, then close
        self.set_timer(2.0, self._close_screen)

    def _update_env_file(self, org_id: int) -> bool:
        """Update the .env file with the new organization ID."""
        env_file_path = ".env"
        
        try:
            lines = []
            key_found = False

            # Read existing lines if file exists
            if os.path.exists(env_file_path):
                with open(env_file_path) as f:
                    lines = f.readlines()

            # Ensure all lines end with newline
            for i, line in enumerate(lines):
                if not line.endswith('\n'):
                    lines[i] = line + '\n'

            # Update existing CODEGEN_ORG_ID or note that we need to add it
            for i, line in enumerate(lines):
                if line.strip().startswith("CODEGEN_ORG_ID="):
                    lines[i] = f"CODEGEN_ORG_ID={org_id}\n"
                    key_found = True
                    break

            # Add new line if not found
            if not key_found:
                lines.append(f"CODEGEN_ORG_ID={org_id}\n")

            # Write back to file
            with open(env_file_path, "w") as f:
                f.writelines(lines)
            
            return True
            
        except Exception:
            return False

    def _close_screen(self) -> None:
        """Close the screen."""
        try:
            # Pop ourselves from the screen stack
            self.app.pop_screen()
        except Exception:
            # Fallback - try to dismiss the screen
            self.dismiss()

    def action_quit(self) -> None:
        """Quit the application or close the screen."""
        self._close_screen()


class OrgSelectorApp(App):
    """Standalone app wrapper for the organization selector."""
    
    CSS_PATH = "../../tui/codegen_theme.tcss"  # Use custom Codegen theme
    TITLE = "Organization Selector - Codegen CLI"
    BINDINGS = [
        Binding("escape,ctrl+c", "quit", "Quit", priority=True),
        Binding("enter", "select_org", "Select", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.organizations = get_cached_organizations() or []
        self.current_org_id = get_current_org_id()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        
        if not self.organizations:
            yield Container(
                Static("⚠️  No organizations found. Please run 'codegen login' first.", classes="warning-message"), 
                id="no-orgs-warning"
            )
        else:
            with Vertical():
                yield Static("🏢 Select Your Organization", classes="title")
                yield Static("Use ↑↓ to navigate, Enter to select, Q/Esc to quit", classes="help")
                
                table = DataTable(id="orgs-table", cursor_type="row")
                table.add_columns("Current", "ID", "Organization Name")
                
                # Get the actual current org ID (checks environment variables first)
                actual_current_org_id = resolve_org_id()
                
                for org in self.organizations:
                    org_id = org["id"]
                    org_name = org["name"]
                    is_current = "●" if org_id == actual_current_org_id else " "
                    
                    table.add_row(is_current, str(org_id), org_name, key=str(org_id))
                
                yield table
                
                yield Static(
                    "\n💡 Selecting an organization will update your CODEGEN_ORG_ID environment variable.", 
                    classes="help"
                )
        
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app mounts."""
        # Set focus on the table if it exists
        if self.organizations:
            try:
                table = self.query_one("#orgs-table", DataTable)
                table.focus()
            except Exception:
                pass

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle DataTable row selection (Enter key)."""
        if event.data_table.id == "orgs-table":
            self._handle_org_selection()

    def action_select_org(self) -> None:
        """Select the highlighted organization (fallback action)."""
        self._handle_org_selection()

    def _handle_org_selection(self) -> None:
        """Handle organization selection logic."""
        if not self.organizations:
            self.notify("❌ No organizations available", severity="error")
            return

        try:
            table = self.query_one("#orgs-table", DataTable)
            
            if table.cursor_row is not None and table.cursor_row < len(self.organizations):
                # Get the selected organization directly from the cursor position
                selected_org = self.organizations[table.cursor_row]
                selected_org_id = selected_org["id"]

                # Set the organization
                self._set_organization(selected_org_id, selected_org["name"])
            else:
                self.notify(f"❌ Invalid cursor position: {table.cursor_row}/{len(self.organizations)}", severity="error")
        except Exception as e:
            self.notify(f"❌ Error in select org: {e}", severity="error")

    def _set_organization(self, org_id: int, org_name: str) -> None:
        """Set the selected organization as default."""
        # Set environment variable
        os.environ["CODEGEN_ORG_ID"] = str(org_id)
        
        # Try to update .env file
        env_updated = self._update_env_file(org_id)
        
        if env_updated:
            self.notify(f"✓ Set default organization: {org_name} (ID: {org_id})")
            self.notify("✓ Updated .env file with CODEGEN_ORG_ID")
        else:
            self.notify(f"✓ Set organization: {org_name} (ID: {org_id})")
            self.notify("ℹ  Add 'export CODEGEN_ORG_ID={org_id}' to your shell for persistence")
        
        # Wait a moment for user to see the notifications, then exit
        self.set_timer(2.0, self.exit)

    def _update_env_file(self, org_id: int) -> bool:
        """Update the .env file with the new organization ID."""
        env_file_path = ".env"
        
        try:
            lines = []
            key_found = False

            # Read existing lines if file exists
            if os.path.exists(env_file_path):
                with open(env_file_path) as f:
                    lines = f.readlines()

            # Ensure all lines end with newline
            for i, line in enumerate(lines):
                if not line.endswith('\n'):
                    lines[i] = line + '\n'

            # Update existing CODEGEN_ORG_ID or note that we need to add it
            for i, line in enumerate(lines):
                if line.strip().startswith("CODEGEN_ORG_ID="):
                    lines[i] = f"CODEGEN_ORG_ID={org_id}\n"
                    key_found = True
                    break

            # Add new line if not found
            if not key_found:
                lines.append(f"CODEGEN_ORG_ID={org_id}\n")

            # Write back to file
            with open(env_file_path, "w") as f:
                f.writelines(lines)
            
            return True
            
        except Exception:
            return False

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()