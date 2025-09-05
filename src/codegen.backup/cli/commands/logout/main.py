import rich

from codegen.cli.auth.token_manager import TokenManager
from codegen.shared.logging.get_logger import get_logger

# Initialize logger
logger = get_logger(__name__)


def logout():
    """Clear stored authentication token."""
    logger.info("Logout command invoked", extra={"operation": "auth.logout", "command": "codegen logout"})

    try:
        token_manager = TokenManager()
        token_manager.clear_token()
        logger.info("Logout completed successfully", extra={"operation": "auth.logout", "success": True})
        rich.print("Successfully logged out")
    except Exception as e:
        logger.error("Logout failed", extra={"operation": "auth.logout", "error_type": type(e).__name__, "error_message": str(e), "success": False}, exc_info=True)
        raise
