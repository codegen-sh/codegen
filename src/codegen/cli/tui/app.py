"""Minimal TUI interface for Codegen CLI."""

import signal
import sys
import termios
import tty
from datetime import datetime
from typing import Any

from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.utils.org import resolve_org_id


class MinimalTUI:
    """Minimal non-full-screen TUI for browsing agent runs."""

    def __init__(self):
        self.token = get_current_token()
        self.is_authenticated = bool(self.token)
        if self.is_authenticated:
            self.org_id = resolve_org_id()
        self.agent_runs: list[dict[str, Any]] = []
        self.selected_index = 0
        self.running = True
        self.show_action_menu = False
        self.action_menu_selection = 0

        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully without clearing screen."""
        self.running = False
        print("\n")  # Just add a newline and exit
        sys.exit(0)

    def _load_agent_runs(self) -> bool:
        """Load the last 10 agent runs."""
        if not self.token or not self.org_id:
            return False

        try:
            import requests

            from codegen.cli.api.endpoints import API_ENDPOINT

            headers = {"Authorization": f"Bearer {self.token}"}

            # Get current user ID
            user_response = requests.get(f"{API_ENDPOINT.rstrip('/')}/v1/users/me", headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            user_id = user_data.get("id")

            # Fetch agent runs - limit to 10
            params = {
                "source_type": "API",
                "limit": 10,
            }

            if user_id:
                params["user_id"] = user_id

            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/runs"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            response_data = response.json()

            self.agent_runs = response_data.get("items", [])
            return True

        except Exception as e:
            print(f"Error loading agent runs: {e}")
            return False

    def _format_status(self, status: str) -> str:
        """Format status with colored indicators."""
        status_map = {
            "COMPLETE": "\033[32m●\033[0m Complete",  # Green
            "ACTIVE": "\033[33m●\033[0m Active",  # Yellow
            "RUNNING": "\033[36m●\033[0m Running",  # Cyan
            "CANCELLED": "\033[90m●\033[0m Cancelled",  # Dark gray
            "ERROR": "\033[31m●\033[0m Error",  # Red
            "FAILED": "\033[31m●\033[0m Failed",  # Red
            "STOPPED": "\033[90m●\033[0m Stopped",  # Dark gray
            "PENDING": "\033[37m●\033[0m Pending",  # Light gray
        }
        return status_map.get(status, f"\033[37m●\033[0m {status}")

    def _format_date(self, created_at: str) -> str:
        """Format creation date."""
        if not created_at or created_at == "Unknown":
            return "Unknown"

        try:
            dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            return dt.strftime("%m/%d %H:%M")
        except (ValueError, TypeError):
            return created_at[:16] if len(created_at) > 16 else created_at

    def _display_header(self):
        """Display the minimal header."""
        print("🤖 \033[1mRecents\033[0m")
        print()

    def _display_agent_list(self):
        """Display the list of agent runs."""
        if not self.agent_runs:
            print("No agent runs found.")
            return

        for i, agent_run in enumerate(self.agent_runs):
            # Highlight selected item
            prefix = "→ " if i == self.selected_index and not self.show_action_menu else "  "

            status = self._format_status(agent_run.get("status", "Unknown"))
            created = self._format_date(agent_run.get("created_at", "Unknown"))
            summary = agent_run.get("summary", "No summary") or "No summary"
            agent_id = agent_run.get("id", "unknown")
            url = f"https://codegen.com/x/{agent_id}"
            # Make URL clickable in terminal
            clickable_url = f"\033]8;;{url}\033\\codegen.com/x/{agent_id}\033]8;;\033\\"

            # Truncate summary to fit with URL
            if len(summary) > 35:
                summary = summary[:32] + "..."

            # Color coding: indigo blue for selected, darker gray for others
            if i == self.selected_index and not self.show_action_menu:
                # Dark blue (similar to text-indigo-700) for selected row
                line = f"\033[34m{prefix}{created:<10} {status:<12} {summary:<38} {clickable_url}\033[0m"
            else:
                # Darker gray for non-selected rows
                line = f"\033[90m{prefix}{created:<10} {status:<12} {summary:<38} {clickable_url}\033[0m"

            print(line)

            # Show action menu right below the selected row if it's expanded
            if i == self.selected_index and self.show_action_menu:
                self._display_inline_action_menu(agent_run)

    def _display_inline_action_menu(self, agent_run: dict):
        """Display action menu inline below the selected row."""
        options = ["pull locally", "open in web"]

        for i, option in enumerate(options):
            if i == self.action_menu_selection:
                # Highlight selected option in blue
                print(f"    \033[34m→ {option}\033[0m")
            else:
                # Unselected options in gray
                print(f"    \033[90m  {option}\033[0m")

        print("\033[90m    Use ↑↓ to navigate, Enter to select, Esc to close\033[0m")

    def _get_char(self):
        """Get a single character from stdin, handling arrow keys."""
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setcbreak(fd)
                ch = sys.stdin.read(1)

                # Handle escape sequences (arrow keys)
                if ch == "\x1b":  # ESC
                    ch2 = sys.stdin.read(1)
                    if ch2 == "[":
                        ch3 = sys.stdin.read(1)
                        return f"\x1b[{ch3}"
                    else:
                        return ch + ch2
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except (ImportError, OSError, termios.error):
            # Fallback for systems where tty manipulation doesn't work
            print("\nUse: ↑(w)/↓(s) navigate, Enter details, R refresh, Q quit")
            try:
                return input("> ").strip()[:1].lower() or "\n"
            except KeyboardInterrupt:
                return "q"

    def _handle_keypress(self, key: str):
        """Handle key presses for navigation."""
        if key.lower() == "q" or key == "\x03":  # q or Ctrl+C
            self.running = False
        elif self.show_action_menu:
            # Handle action menu navigation
            if key == "\x1b[A" or key.lower() == "w":  # Up arrow or W
                self.action_menu_selection = max(0, self.action_menu_selection - 1)
            elif key == "\x1b[B" or key.lower() == "s":  # Down arrow or S
                self.action_menu_selection = min(1, self.action_menu_selection + 1)  # 2 options: 0,1
            elif key == "\r" or key == "\n":  # Enter
                self._execute_inline_action()
                self.show_action_menu = False  # Close menu after action
            elif key == "\x1b" or key.lower() == "escape":  # Escape
                self.show_action_menu = False  # Close menu
                self.action_menu_selection = 0  # Reset selection
        else:
            # Handle main list navigation
            if key == "\x1b[A" or key.lower() == "w":  # Up arrow or W
                self.selected_index = max(0, self.selected_index - 1)
                self.show_action_menu = False  # Close any open menu
                self.action_menu_selection = 0
            elif key == "\x1b[B" or key.lower() == "s":  # Down arrow or S
                self.selected_index = min(len(self.agent_runs) - 1, self.selected_index + 1)
                self.show_action_menu = False  # Close any open menu
                self.action_menu_selection = 0
            elif key == "\r" or key == "\n" or key.lower() == "e":  # Enter or E
                self.show_action_menu = True  # Open action menu
                self.action_menu_selection = 0  # Reset to first option
            elif key.lower() == "r":
                self._refresh()
                self.show_action_menu = False  # Close menu on refresh
                self.action_menu_selection = 0
            elif len(key) > 1:  # Handle any other escape sequences
                pass  # Ignore unknown escape sequences

    def _execute_inline_action(self):
        """Execute the selected action from the inline menu."""
        if not (0 <= self.selected_index < len(self.agent_runs)):
            return

        agent_run = self.agent_runs[self.selected_index]
        agent_id = agent_run.get("id", "unknown")
        url = f"https://codegen.com/x/{agent_id}"
        options = ["pull", "open in web"]

        if 0 <= self.action_menu_selection < len(options):
            action = options[self.action_menu_selection]
            if action == "pull":
                # Placeholder for pull functionality
                print(f"\n🔄 Pull functionality not yet implemented for agent {agent_id}")
                input("Press Enter to continue...")
            elif action == "open in web":
                try:
                    import webbrowser

                    webbrowser.open(url)
                    print(f"\n🌐 Opened {url} in your default browser")
                except Exception as e:
                    print(f"\n❌ Failed to open browser: {e}")
                input("Press Enter to continue...")

    def _open_agent_details(self):
        """Toggle the inline action menu."""
        self.show_action_menu = not self.show_action_menu
        if not self.show_action_menu:
            self.action_menu_selection = 0  # Reset selection when closing

    def _refresh(self):
        """Refresh the agent runs list."""
        if self._load_agent_runs():
            self.selected_index = 0  # Reset selection

    def _clear_and_redraw(self):
        """Clear screen and redraw everything."""
        # Move cursor to top and clear screen from cursor down
        print("\033[H\033[J", end="")
        self._display_header()
        self._display_agent_list()
        if self.show_action_menu:
            print("\n\033[90m(arrows) navigate menu, [Enter] select, [Esc] close, [Q] quit\033[0m")
        else:
            print("\n\033[90m(arrows) navigate, [Enter] actions, [R] refresh, [Q] quit\033[0m")

    def run(self):
        """Run the minimal TUI."""
        if not self.is_authenticated:
            print("⚠️  Not authenticated. Please run 'codegen login' first.")
            return

        print("Loading...")
        if not self._load_agent_runs():
            print("Failed to load agent runs. Please check your authentication and try again.")
            return

        # Initial display
        self._clear_and_redraw()

        # Main event loop
        while self.running:
            try:
                key = self._get_char()
                self._handle_keypress(key)
                if self.running:  # Only redraw if we're still running
                    self._clear_and_redraw()
            except KeyboardInterrupt:
                # This should be handled by the signal handler, but just in case
                break

        print()  # Add newline before exiting


def run_tui():
    """Run the minimal Codegen TUI."""
    tui = MinimalTUI()
    tui.run()
