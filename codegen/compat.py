# C:\Programs\codegen\src\codegen\compat.py
"""Compatibility layer for Unix-specific modules on Windows."""

import sys
import types

# Mock termios for Windows
if sys.platform == "win32":
    termios = types.ModuleType("termios")
    termios.tcgetattr = lambda fd: [0] * 6
    termios.tcsetattr = lambda fd, when, flags: None
    termios.TCSANOW = 0
    termios.TCSADRAIN = 0
    termios.TCSAFLUSH = 0
    termios.error = OSError
    sys.modules["termios"] = termios

# Mock tty for Windows
if sys.platform == "win32":
    # Create a mock tty module that doesn't import termios
    tty = types.ModuleType("tty")
    tty.setcbreak = lambda fd: None
    tty.setraw = lambda fd: None
    # Mock other tty functions if needed
    sys.modules["tty"] = tty

# Mock curses for Windows
if sys.platform == "win32":
    curses = types.ModuleType("curses")
    curses.noecho = lambda: None
    curses.cbreak = lambda: None
    curses.curs_set = lambda x: None
    curses.KEY_UP = 0
    curses.KEY_DOWN = 0
    curses.KEY_LEFT = 0
    curses.KEY_RIGHT = 0
    curses.A_BOLD = 0
    curses.A_NORMAL = 0
    curses.A_REVERSE = 0
    curses.A_DIM = 0
    curses.A_BLINK = 0
    curses.A_INVIS = 0
    curses.A_PROTECT = 0
    curses.A_CHARTEXT = 0
    curses.A_COLOR = 0
    curses.ERR = -1
    sys.modules["curses"] = curses

# Mock fcntl for Windows
if sys.platform == "win32":
    fcntl = types.ModuleType("fcntl")
    fcntl.flock = lambda fd, operation: None
    sys.modules["fcntl"] = fcntl

# Mock signal for Windows
if sys.platform == "win32":
    signal = types.ModuleType("signal")
    signal.SIGINT = 2
    signal.SIGTERM = 15
    signal.SIG_DFL = 0
    signal.SIG_IGN = 1
    signal.signal = lambda signum, handler: handler
    sys.modules["signal"] = signal
