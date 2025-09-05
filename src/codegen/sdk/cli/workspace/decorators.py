import functools
import sys
from collections.abc import Callable

from codegen.sdk.cli.auth.session import CliSession
from codegen.sdk.cli.rich.pretty_print import pretty_print_error


def requires_init(f: Callable) -> Callable:
    """Decorator that ensures codegen has been initialized."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Create a session if one wasn't provided
        session = kwargs.get("session") or CliSession.from_active_session()
        if session is None:
            pretty_print_error("Graph-sitter not initialized. Please run `gs init` from a git repo workspace.")
            sys.exit(1)

        kwargs["session"] = session
        return f(*args, **kwargs)

    return wrapper
