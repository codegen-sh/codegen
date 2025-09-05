import sys
from typing import Iterable


def inplace_print(lines: Iterable[str], prev_lines_rendered: int) -> int:
    """Redraw a small block of text in-place without scrolling.

    Args:
            lines: The lines to render (each should NOT include a trailing newline)
            prev_lines_rendered: How many lines were rendered in the previous frame. Pass 0 on first call.

    Returns:
            The number of lines rendered this call. Use as prev_lines_rendered on the next call.
    """
    # Move cursor up to the start of the previous block (if any)
    if prev_lines_rendered > 0:
        sys.stdout.write(f"\x1b[{prev_lines_rendered}F")  # Cursor up N lines

    # Rewrite each line, clearing it first to avoid remnants from previous content
    count = 0
    for line in lines:
        sys.stdout.write("\x1b[2K\r")  # Clear entire line and return carriage
        sys.stdout.write(f"{line}\n")
        count += 1

    sys.stdout.flush()
    return count
