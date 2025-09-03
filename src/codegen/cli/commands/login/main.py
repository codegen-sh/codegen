import typer

from codegen.cli.auth.login import login_routine
from codegen.cli.auth.token_manager import get_current_token
from codegen.shared.logging.get_logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def _get_session_context() -> dict:
    """Get session context for logging."""
    try:
        from codegen.cli.telemetry.otel_setup import get_session_uuid

        return {"session_id": get_session_uuid()}
    except ImportError:
        return {}


def login(token: str | None = typer.Option(None, help="API token for authentication")):
    """Store authentication token."""
    extra = {"operation": "auth.login", "has_provided_token": bool(token), "command": "codegen login", **_get_session_context()}
    logger.info("Login command invoked", extra=extra)

    # Check if already authenticated
    current_token = get_current_token()
    if current_token:
        logger.debug("User already authenticated", extra={"operation": "auth.login", "already_authenticated": True, **_get_session_context()})
        pass  # Just proceed silently with re-authentication

    try:
        login_routine(token)
        logger.info("Login completed successfully", extra={"operation": "auth.login", "success": True, **_get_session_context()})
    except Exception as e:
        logger.error("Login failed", extra={"operation": "auth.login", "error_type": type(e).__name__, "error_message": str(e), "success": False, **_get_session_context()}, exc_info=True)
        raise
