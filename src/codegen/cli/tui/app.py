"""Minimal TUI interface for Codegen CLI."""

import signal
import sys
import termios
import tty
from datetime import datetime
from typing import Any

import requests
import typer

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.commands.agent.main import pull
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

        # Tab management
        self.tabs = ["recents", "new", "web"]
        self.current_tab = 0

        # New tab state
        self.prompt_input = ""
        self.cursor_position = 0
        self.input_mode = False  # When true, we're typing in the input box

        # Set up signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)

    def _get_webapp_domain(self) -> str:
        """Get the webapp domain based on environment."""
        # Simple environment detection - can be expanded later
        import os

        env = os.getenv("ENV", "staging").lower()

        if env == "production":
            return "codegen.com"
        elif env == "local":
            return "localhost:3000"
        else:  # staging or default
            return "chadcode.sh"

    def _generate_agent_url(self, agent_id: str) -> str:
        """Generate the complete agent URL."""
        domain = self._get_webapp_domain()
        protocol = "http" if "localhost" in domain else "https"
        return f"{protocol}://{domain}/x/{agent_id}"

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

    def _format_status(self, status: str, agent_run: dict | None = None) -> str:
        """Format status with colored indicators matching kanban style."""
        # Check if this agent has a merged PR (done status)
        is_done = False
        if agent_run:
            github_prs = agent_run.get("github_pull_requests", [])
            for pr in github_prs:
                if pr.get("state") == "closed" and pr.get("merged", False):
                    is_done = True
                    break

        if is_done:
            return "\033[34m✓\033[0m Done"  # Blue checkmark for merged PR

        status_map = {
            "COMPLETE": "\033[38;2;52;211;153m○\033[0m Complete",  # emerald-400
            "ACTIVE": "\033[38;2;162;119;255m●\033[0m Active",  # #a277ff (purple from badge)
            "RUNNING": "\033[38;2;162;119;255m●\033[0m Running",  # #a277ff (purple from badge)
            "ERROR": "\033[38;2;248;113;113m●\033[0m Error",  # red-400
            "FAILED": "\033[38;2;248;113;113m●\033[0m Failed",  # red-400
            "CANCELLED": "\033[38;2;156;163;175m○\033[0m Cancelled",  # gray-400
            "STOPPED": "\033[38;2;156;163;175m○\033[0m Stopped",  # gray-400
            "PENDING": "\033[38;2;156;163;175m○\033[0m Pending",  # gray-400
            "TIMEOUT": "\033[38;2;251;146;60m●\033[0m Timeout",  # orange-400
            "MAX_ITERATIONS_REACHED": "\033[38;2;251;191;36m●\033[0m Max Iterations",  # amber-400
            "OUT_OF_TOKENS": "\033[38;2;251;191;36m●\033[0m Out of Tokens",  # amber-400
            "EVALUATION": "\033[38;2;196;181;253m●\033[0m Evaluation",  # purple-400
        }
        return status_map.get(status, f"\033[37m○\033[0m {status}")

    def _strip_ansi_codes(self, text: str) -> str:
        """Strip ANSI color codes from text."""
        import re

        ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        return ansi_escape.sub("", text)

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
        """Display the header with tabs."""
        # Simple header with indigo slashes and Codegen text
        print("\033[38;2;82;19;217m" + "/" * 20 + " Codegen\033[0m")
        print()  # Add blank line between header and tabs

        # Display tabs
        tab_line = ""
        for i, tab in enumerate(self.tabs):
            if i == self.current_tab:
                tab_line += f"\033[34m[{tab}]\033[0m  "  # Blue for active tab
            else:
                tab_line += f"\033[90m{tab}\033[0m  "  # Gray for inactive tabs

        print(tab_line)
        print()

    def _display_agent_list(self):
        """Display the list of agent runs."""
        if not self.agent_runs:
            print("No agent runs found.")
            return

        for i, agent_run in enumerate(self.agent_runs):
            # Highlight selected item
            prefix = "→ " if i == self.selected_index and not self.show_action_menu else "  "

            status = self._format_status(agent_run.get("status", "Unknown"), agent_run)
            created = self._format_date(agent_run.get("created_at", "Unknown"))
            summary = agent_run.get("summary", "No summary") or "No summary"

            # No need to truncate summary as much since we removed the URL column
            if len(summary) > 60:
                summary = summary[:57] + "..."

            # Color coding: indigo blue for selected, darker gray for others (but keep status colors)
            if i == self.selected_index and not self.show_action_menu:
                # Blue timestamp and summary for selected row, but preserve status colors
                line = f"\033[34m{prefix}{created:<10}\033[0m {status} \033[34m{summary}\033[0m"
            else:
                # Gray text for non-selected rows, but preserve status colors
                line = f"\033[90m{prefix}{created:<10}\033[0m {status} \033[90m{summary}\033[0m"

            print(line)

            # Show action menu right below the selected row if it's expanded
            if i == self.selected_index and self.show_action_menu:
                self._display_inline_action_menu(agent_run)

    def _display_new_tab(self):
        """Display the new agent creation interface."""
        print("Create a new agent run:")
        print()

        # Input prompt label
        print("Prompt:")

        # Get terminal width, default to 80 if can't determine
        try:
            import os

            terminal_width = os.get_terminal_size().columns
        except (OSError, AttributeError):
            terminal_width = 80

        # Calculate input box width (leave some margin)
        box_width = max(60, terminal_width - 4)

        # Input box with cursor
        input_display = self.prompt_input
        if self.input_mode:
            # Add cursor indicator when in input mode
            if self.cursor_position <= len(input_display):
                input_display = input_display[: self.cursor_position] + "█" + input_display[self.cursor_position :]

        # Handle long input that exceeds box width
        if len(input_display) > box_width - 4:
            # Show portion around cursor
            start_pos = max(0, self.cursor_position - (box_width // 2))
            input_display = input_display[start_pos : start_pos + box_width - 4]

        # Display full-width input box with simple border like Claude Code
        border_style = "\033[34m" if self.input_mode else "\033[90m"  # Blue when active, gray when inactive
        reset = "\033[0m"

        print(border_style + "┌" + "─" * (box_width - 2) + "┐" + reset)
        padding = box_width - 4 - len(input_display.replace("█", ""))
        print(border_style + "│" + reset + f" {input_display}{' ' * max(0, padding)} " + border_style + "│" + reset)
        print(border_style + "└" + "─" * (box_width - 2) + "┘" + reset)
        print()

        if self.input_mode:
            print("\033[90mType your prompt • [Enter] create agent • [Esc] cancel\033[0m")
        else:
            print("\033[90m[Enter] start typing • [Tab] switch tabs • [Q] quit\033[0m")

    def _create_background_agent(self, prompt: str):
        """Create a background agent run."""
        if not self.token or not self.org_id:
            print("\n❌ Not authenticated or no organization configured.")
            input("Press Enter to continue...")
            return

        if not prompt.strip():
            print("\n❌ Please enter a prompt.")
            input("Press Enter to continue...")
            return

        print(f"\n🔄 Creating agent run with prompt: '{prompt[:50]}{'...' if len(prompt) > 50 else ''}'")

        try:
            payload = {"prompt": prompt.strip()}
            headers = {
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
                "x-codegen-client": "codegen__claude_code",
            }
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{self.org_id}/agent/run"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            agent_run_data = response.json()

            run_id = agent_run_data.get("id", "Unknown")
            status = agent_run_data.get("status", "Unknown")
            web_url = self._generate_agent_url(run_id)

            print("\n✅ Agent run created successfully!")
            print(f"   Run ID: {run_id}")
            print(f"   Status: {status}")
            print(f"   Web URL: {web_url}")

            # Clear the input
            self.prompt_input = ""
            self.cursor_position = 0
            self.input_mode = False

            # Optionally refresh the recents tab if we're going back to it
            if hasattr(self, "_load_agent_runs"):
                print("\n🔄 Refreshing recents...")
                self._load_agent_runs()

        except Exception as e:
            print(f"\n❌ Failed to create agent run: {e}")

        input("\nPress Enter to continue...")

    def _display_web_tab(self):
        """Display the web interface access tab."""
        print("Open Web Interface:")
        print()
        print("  \033[34m→ Open Web (localhost:3000/me)\033[0m")
        print()
        print("Press Enter to open the web interface in your browser.")

    def _pull_agent_branch(self, agent_id: str):
        """Pull the PR branch for an agent run locally."""
        print(f"\n🔄 Pulling PR branch for agent {agent_id}...")
        print("─" * 50)

        try:
            # Call the existing pull command with the agent_id
            pull(agent_id=int(agent_id), org_id=self.org_id)

        except typer.Exit as e:
            # typer.Exit is expected for both success and failure cases
            if e.exit_code == 0:
                print("\n✅ Pull completed successfully!")
            else:
                print(f"\n❌ Pull failed (exit code: {e.exit_code})")
        except ValueError:
            print(f"\n❌ Invalid agent ID: {agent_id}")
        except Exception as e:
            print(f"\n❌ Unexpected error during pull: {e}")

        print("─" * 50)
        input("Press Enter to continue...")

    def _display_content(self):
        """Display content based on current tab."""
        if self.current_tab == 0:  # recents
            self._display_agent_list()
        elif self.current_tab == 1:  # new
            self._display_new_tab()
        elif self.current_tab == 2:  # web
            self._display_web_tab()

    def _display_inline_action_menu(self, agent_run: dict):
        """Display action menu inline below the selected row."""
        agent_id = agent_run.get("id", "unknown")
        web_url = self._generate_agent_url(agent_id)
        # Extract just the domain/path part without protocol for display
        display_url = web_url.replace("https://", "").replace("http://", "")

        # Check if there are GitHub PRs associated with this agent run
        github_prs = agent_run.get("github_pull_requests", [])

        # Start with basic web option
        options = [f"open in web ({display_url})"]

        # Only add pull locally if there are PRs
        if github_prs:
            options.insert(0, "pull locally")  # Add as first option

        # Add PR option if available
        if github_prs:
            pr_url = github_prs[0].get("url", "")
            if pr_url:
                # Extract just the GitHub part for display
                pr_display = pr_url.replace("https://github.com/", "github.com/")
                options.append(f"open PR ({pr_display})")

        for i, option in enumerate(options):
            if i == 0:
                # Always highlight first (top) option in blue
                print(f"    \033[34m→ {option}\033[0m")
            else:
                # All other options in gray
                print(f"    \033[90m  {option}\033[0m")

        print("\033[90m    [Enter] select, [C] close\033[0m")

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
        # Global quit
        if key.lower() == "q" or key == "\x03":  # q or Ctrl+C
            self.running = False
            return

        # Tab switching (unless in input mode)
        if not self.input_mode and key == "\t":  # Tab key
            self.current_tab = (self.current_tab + 1) % len(self.tabs)
            # Reset state when switching tabs
            self.show_action_menu = False
            self.action_menu_selection = 0
            self.selected_index = 0
            return

        # Handle based on current context
        if self.input_mode:
            self._handle_input_mode_keypress(key)
        elif self.show_action_menu:
            self._handle_action_menu_keypress(key)
        elif self.current_tab == 0:  # recents tab
            self._handle_recents_keypress(key)
        elif self.current_tab == 1:  # new tab
            self._handle_new_tab_keypress(key)
        elif self.current_tab == 2:  # web tab
            self._handle_web_tab_keypress(key)

    def _handle_input_mode_keypress(self, key: str):
        """Handle keypresses when in text input mode."""
        if key.lower() == "c":  # 'C' key - exit input mode
            self.input_mode = False
        elif key == "\r" or key == "\n":  # Enter - create agent run
            if self.prompt_input.strip():  # Only create if there's actual content
                self._create_background_agent(self.prompt_input)
            else:
                self.input_mode = False  # Exit input mode if empty
        elif key == "\x7f" or key == "\b":  # Backspace
            if self.cursor_position > 0:
                self.prompt_input = self.prompt_input[: self.cursor_position - 1] + self.prompt_input[self.cursor_position :]
                self.cursor_position -= 1
        elif key == "\x1b[C":  # Right arrow
            self.cursor_position = min(len(self.prompt_input), self.cursor_position + 1)
        elif key == "\x1b[D":  # Left arrow
            self.cursor_position = max(0, self.cursor_position - 1)
        elif len(key) == 1 and key.isprintable():  # Regular character
            self.prompt_input = self.prompt_input[: self.cursor_position] + key + self.prompt_input[self.cursor_position :]
            self.cursor_position += 1

    def _handle_action_menu_keypress(self, key: str):
        """Handle action menu keypresses."""
        if key == "\r" or key == "\n":  # Enter
            self._execute_inline_action()
            self.show_action_menu = False  # Close menu after action
        elif key.lower() == "c" or key == "\x1b[D":  # 'C' key or Left arrow to close
            self.show_action_menu = False  # Close menu
            self.action_menu_selection = 0  # Reset selection

    def _handle_recents_keypress(self, key: str):
        """Handle keypresses in the recents tab."""
        if key == "\x1b[A" or key.lower() == "w":  # Up arrow or W
            self.selected_index = max(0, self.selected_index - 1)
            self.show_action_menu = False  # Close any open menu
            self.action_menu_selection = 0
        elif key == "\x1b[B" or key.lower() == "s":  # Down arrow or S
            self.selected_index = min(len(self.agent_runs) - 1, self.selected_index + 1)
            self.show_action_menu = False  # Close any open menu
            self.action_menu_selection = 0
        elif key == "\x1b[C":  # Right arrow - open action menu
            self.show_action_menu = True  # Open action menu
            self.action_menu_selection = 0  # Reset to first option
        elif key == "\x1b[D":  # Left arrow - close action menu
            self.show_action_menu = False  # Close action menu
            self.action_menu_selection = 0
        elif key == "\r" or key == "\n" or key.lower() == "e":  # Enter or E
            self.show_action_menu = True  # Open action menu
            self.action_menu_selection = 0  # Reset to first option
        elif key.lower() == "r":
            self._refresh()
            self.show_action_menu = False  # Close menu on refresh
            self.action_menu_selection = 0

    def _handle_new_tab_keypress(self, key: str):
        """Handle keypresses in the new tab."""
        if key == "\r" or key == "\n":  # Enter - start input mode
            if not self.input_mode:
                self.input_mode = True
                self.cursor_position = len(self.prompt_input)
            else:
                # If already in input mode, Enter should create the agent
                self._create_background_agent(self.prompt_input)

    def _handle_web_tab_keypress(self, key: str):
        """Handle keypresses in the web tab."""
        if key == "\r" or key == "\n":  # Enter - open web interface
            try:
                import webbrowser

                webbrowser.open("http://localhost:3000/me")
                print("\n✅ Opening web interface in browser...")
            except Exception as e:
                print(f"\n❌ Failed to open browser: {e}")
                input("Press Enter to continue...")

    def _execute_inline_action(self):
        """Execute the selected action from the inline menu."""
        if not (0 <= self.selected_index < len(self.agent_runs)):
            return

        agent_run = self.agent_runs[self.selected_index]
        agent_id = agent_run.get("id", "unknown")
        web_url = self._generate_agent_url(agent_id)

        # Get the available options to map selection to action
        github_prs = agent_run.get("github_pull_requests", [])
        options = ["open in web"]

        if github_prs:
            options.insert(0, "pull locally")  # Add as first option

        if github_prs and github_prs[0].get("url"):
            options.append("open PR")

        # Always execute the first (top) option
        if len(options) > 0:
            selected_option = options[0]

            if selected_option == "pull locally":
                self._pull_agent_branch(agent_id)
            elif selected_option.startswith("open in web"):
                try:
                    import webbrowser

                    webbrowser.open(web_url)
                    # No pause - let it flow back naturally to collapsed state
                except Exception as e:
                    print(f"\n❌ Failed to open browser: {e}")
                    input("Press Enter to continue...")  # Only pause on errors
            elif selected_option == "open PR":
                pr_url = github_prs[0]["url"]
                try:
                    import webbrowser

                    webbrowser.open(pr_url)
                    # No pause - seamless flow back to collapsed state
                except Exception as e:
                    print(f"\n❌ Failed to open PR: {e}")
                    input("Press Enter to continue...")  # Only pause on errors

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
        self._display_content()

        # Show appropriate instructions based on context
        if self.input_mode:
            print("\n\033[90mType your prompt • [Enter] create • [C] cancel • [Q] quit\033[0m")
        elif self.show_action_menu:
            print("\n\033[90m[Enter] select • [C] close • [Q] quit\033[0m")
        elif self.current_tab == 0:  # recents
            print("\n\033[90m[Tab] switch tabs • (↑↓) navigate • (←→) open/close • [Enter] actions • [R] refresh • [Q] quit\033[0m")
        elif self.current_tab == 1:  # new
            print("\n\033[90m[Tab] switch tabs • [Enter] start typing • [Q] quit\033[0m")
        elif self.current_tab == 2:  # web
            print("\n\033[90m[Tab] switch tabs • [Enter] open web • [Q] quit\033[0m")

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
