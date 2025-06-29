import rich

from codegen.cli.auth.token_manager import TokenManager


def logout():
    """Clear stored authentication token."""
    token_manager = TokenManager()
    token_manager.clear_token()
    rich.print("Successfully logged out")
