# C:\Programs\codegen\src\codegen\cli\tui\windows_app.py
"""Windows-compatible TUI implementation."""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table


class WindowsTUI:
    """Simple Windows-compatible TUI."""

    def __init__(self):
        self.console = Console()
        self.current_view = "main"
        self.data = {}

    def run(self):
        """Run the TUI."""
        self.console.print(Panel("Codegen TUI", style="bold blue"))
        self.console.print("Press 'h' for help, 'q' to quit")

        while True:
            if self.current_view == "main":
                self._show_main_view()
            elif self.current_view == "help":
                self._show_help_view()
            elif self.current_view == "agents":
                self._show_agents_view()
            elif self.current_view == "repos":
                self._show_repos_view()
            elif self.current_view == "orgs":
                self._show_orgs_view()

            try:
                cmd = Prompt.ask("\nCommand")
                if cmd.lower() == "q":
                    break
                elif cmd.lower() == "h":
                    self.current_view = "help"
                elif cmd.lower() == "m":
                    self.current_view = "main"
                elif cmd.lower() == "a":
                    self.current_view = "agents"
                elif cmd.lower() == "r":
                    self.current_view = "repos"
                elif cmd.lower() == "o":
                    self.current_view = "orgs"
                else:
                    self.console.print(f"Unknown command: {cmd}")
            except KeyboardInterrupt:
                break

    def _show_main_view(self):
        """Show the main view."""
        self.console.clear()
        self.console.print(Panel("Codegen Main Menu", style="bold blue"))
        self.console.print("a - View Agents")
        self.console.print("r - View Repositories")
        self.console.print("o - View Organizations")
        self.console.print("h - Help")
        self.console.print("q - Quit")

    def _show_help_view(self):
        """Show the help view."""
        self.console.clear()
        self.console.print(Panel("Codegen Help", style="bold blue"))
        self.console.print("a - View Agents - List all available agents")
        self.console.print("r - View Repositories - List all repositories")
        self.console.print("o - View Organizations - List all organizations")
        self.console.print("m - Main menu")
        self.console.print("q - Quit")
        self.console.print("\nPress 'm' to return to main menu")

    def _show_agents_view(self):
        """Show the agents view."""
        self.console.clear()
        self.console.print(Panel("Codegen Agents", style="bold blue"))
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Status", style="green")

        # Add sample data
        table.add_row("1", "Code Review Agent", "Active")
        table.add_row("2", "Bug Fixer Agent", "Active")
        table.add_row("3", "Documentation Agent", "Inactive")

        self.console.print(table)
        self.console.print("\nPress 'm' to return to main menu")

    def _show_repos_view(self):
        """Show the repositories view."""
        self.console.clear()
        self.console.print(Panel("Codegen Repositories", style="bold blue"))
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Name", style="bold")
        table.add_column("URL", style="cyan")
        table.add_column("Status", style="green")

        # Add sample data
        table.add_row("my-project", "https://github.com/user/my-project", "Active")
        table.add_row(
            "another-project", "https://github.com/user/another-project", "Active"
        )

        self.console.print(table)
        self.console.print("\nPress 'm' to return to main menu")

    def _show_orgs_view(self):
        """Show the organizations view."""
        self.console.clear()
        self.console.print(Panel("Codegen Organizations", style="bold blue"))
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("ID", style="dim")
        table.add_column("Name", style="bold")
        table.add_column("Status", style="green")

        # Add sample data
        table.add_row("1", "My Organization", "Active")
        table.add_row("2", "Another Org", "Inactive")

        self.console.print(table)
        self.console.print("\nPress 'm' to return to main menu")


def run_tui():
    """Run the Windows-compatible TUI."""
    tui = WindowsTUI()
    tui.run()
