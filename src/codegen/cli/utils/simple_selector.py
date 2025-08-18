"""Simple terminal-based selector utility."""

import signal
import sys
import termios
import tty
from typing import Any


def _get_char():
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
        print("\nUse: ↑(w)/↓(s) navigate, Enter select, q quit")
        try:
            return input("> ").strip()[:1].lower() or "\n"
        except KeyboardInterrupt:
            return "q"


def simple_select(title: str, options: list[dict[str, Any]], display_key: str = "name", show_help: bool = True, allow_cancel: bool = True) -> dict[str, Any] | None:
    """Show a simple up/down selector for choosing from options.

    Args:
        title: Title to display above the options
        options: List of option dictionaries
        display_key: Key to use for displaying option text
        show_help: Whether to show navigation help text
        allow_cancel: Whether to allow canceling with Esc/q

    Returns:
        Selected option dictionary or None if canceled
    """
    if not options:
        print("No options available.")
        return None

    if len(options) == 1:
        # Only one option, select it automatically
        return options[0]

    selected = 0
    running = True

    # Set up signal handler for Ctrl+C
    def signal_handler(signum, frame):
        nonlocal running
        running = False
        print("\n")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    try:
        print(f"\n{title}")
        print()

        # Initial display
        for i, option in enumerate(options):
            display_text = str(option.get(display_key, f"Option {i + 1}"))
            if i == selected:
                print(f"  \033[34m→ {display_text}\033[0m")
            else:
                print(f"  \033[90m  {display_text}\033[0m")

        if show_help:
            print()
            help_text = "[Enter] select • [↑↓] navigate"
            if allow_cancel:
                help_text += " • [q/Esc] cancel"
            print(f"\033[90m{help_text}\033[0m")

        while running:
            # Get input
            key = _get_char()

            if key == "\x1b[A" or key.lower() == "w":  # Up arrow or W
                selected = max(0, selected - 1)
                # Redraw options only
                lines_to_move = len(options) + (2 if show_help else 0)
                print(f"\033[{lines_to_move}A", end="")  # Move cursor up to start of options
                for i, option in enumerate(options):
                    display_text = str(option.get(display_key, f"Option {i + 1}"))
                    if i == selected:
                        print(f"  \033[34m→ {display_text}\033[0m\033[K")  # Clear to end of line
                    else:
                        print(f"  \033[90m  {display_text}\033[0m\033[K")  # Clear to end of line
                if show_help:
                    print("\033[K")  # Clear help line
                    print(f"\033[90m{help_text}\033[0m\033[K")  # Redraw help

            elif key == "\x1b[B" or key.lower() == "s":  # Down arrow or S
                selected = min(len(options) - 1, selected + 1)
                # Redraw options only
                lines_to_move = len(options) + (2 if show_help else 0)
                print(f"\033[{lines_to_move}A", end="")  # Move cursor up to start of options
                for i, option in enumerate(options):
                    display_text = str(option.get(display_key, f"Option {i + 1}"))
                    if i == selected:
                        print(f"  \033[34m→ {display_text}\033[0m\033[K")  # Clear to end of line
                    else:
                        print(f"  \033[90m  {display_text}\033[0m\033[K")  # Clear to end of line
                if show_help:
                    print("\033[K")  # Clear help line
                    print(f"\033[90m{help_text}\033[0m\033[K")  # Redraw help

            elif key == "\r" or key == "\n":  # Enter - select option
                return options[selected]
            elif allow_cancel and (key.lower() == "q" or key == "\x1b"):  # q or Esc - cancel
                return None
            elif key == "\x03":  # Ctrl+C
                running = False
                break

    except KeyboardInterrupt:
        return None
    finally:
        # Restore signal handler
        signal.signal(signal.SIGINT, signal.SIG_DFL)

    return None


def simple_org_selector(organizations: list[dict], current_org_id: int | None = None, title: str = "Select Organization") -> dict | None:
    """Show a simple organization selector.

    Args:
        organizations: List of organization dictionaries with 'id' and 'name'
        current_org_id: Currently selected organization ID (for display)
        title: Title to show above selector

    Returns:
        Selected organization dictionary or None if canceled
    """
    if not organizations:
        print("No organizations available.")
        return None

    # Format organizations for display with current indicator
    display_orgs = []
    for org in organizations:
        org_id = org.get("id")
        org_name = org.get("name", f"Organization {org_id}")

        # Add current indicator
        if org_id == current_org_id:
            display_name = f"{org_name} (current)"
        else:
            display_name = org_name

        display_orgs.append(
            {
                **org,  # Keep original org data
                "display_name": display_name,
            }
        )

    return simple_select(title=title, options=display_orgs, display_key="display_name", show_help=True, allow_cancel=True)
