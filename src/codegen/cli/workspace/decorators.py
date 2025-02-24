import functools
import sys
from collections.abc import Callable

from codegen.cli.auth.session import CodegenSession
from codegen.cli.rich.pretty_print import pretty_print_error


def requires_init(f: Callable) -> Callable:
    """Decorator that ensures codegen has been initialized."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        # Create a session if one wasn't provided
        session = kwargs.get("session") or CodegenSession.from_active_session()
        if session is None:
            pretty_print_error("Codegen not initialized. Please run `codegen init` from a git repo workspace.")
            sys.exit(1)

        kwargs["session"] = session
        return f(*args, **kwargs)

    return wrapper
