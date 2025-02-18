import functools
from collections.abc import Callable

import click
import rich

from codegen.cli.auth.login import login_routine
from codegen.cli.auth.session import CodegenSession
from codegen.cli.auth.token_manager import TokenManager, get_current_token
from codegen.cli.errors import AuthError
from codegen.cli.rich.pretty_print import pretty_print_error


def requires_auth(f: Callable) -> Callable:
    """Decorator that ensures a user is authenticated and injects a CodegenSession."""

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        session = CodegenSession.from_active_session()

        # Check for valid session
        if session is None:
            pretty_print_error("There is currently no active session.\nPlease run 'codegen init' to initialize the project.")
            raise click.Abort()

        if (token := get_current_token()) is None:
            rich.print("[yellow]Not authenticated. Let's get you logged in first![/yellow]\n")
            login_routine()
        else:
            try:
                token_manager = TokenManager()
                token_manager.authenticate_token(token)
            except AuthError:
                rich.print("[yellow]Authentication token is invalid or expired. Let's get you logged in again![/yellow]\n")
                login_routine()

        return f(*args, session=session, **kwargs)

    return wrapper
