import logging
import os
import tempfile
from typing import Any, Callable, Optional, TypeVar

from pydantic import BaseModel

from codegen.extensions.events.interface import EventHandlerManagerProtocol
from codegen.extensions.linear.linear_client import LinearClient
from codegen.extensions.linear.types import LinearAttachment, LinearEvent
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class Linear(EventHandlerManagerProtocol):
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}
        self._client = None

    @property
    def client(self) -> LinearClient:
        """Get the Linear client instance."""
        if not self._client:
            access_token = os.environ.get("LINEAR_ACCESS_TOKEN")
            if not access_token:
                msg = "LINEAR_ACCESS_TOKEN environment variable is not set"
                raise ValueError(msg)
            self._client = LinearClient(access_token=access_token)
        return self._client

    def unsubscribe_all_handlers(self):
        logger.info("[HANDLERS] Clearing all handlers")
        self.registered_handlers.clear()

    def event(self, event_name: str):
        """Decorator for registering a Linear event handler.

        Args:
            event_name: The type of event to handle (e.g. 'Issue', 'Comment')
        """
        logger.info(f"[EVENT] Registering handler for {event_name}")

        def register_handler(func: Callable[[LinearEvent], Any]):
            func_name = func.__qualname__
            logger.info(f"[EVENT] Registering function {func_name} for {event_name}")

            def new_func(raw_event: dict):
                # Get event type from payload
                event_type = raw_event.get("type")
                if event_type != event_name:
                    logger.info(f"[HANDLER] Event type mismatch: expected {event_name}, got {event_type}")
                    return None

                # Parse event into LinearEvent type
                event = LinearEvent.model_validate(raw_event)

                # Check if this is an issue event and has attachments
                if event_type == "Issue" and hasattr(event.data, "id"):
                    try:
                        # Get attachments for the issue
                        attachments = self.client.get_issue_attachments(event.data.id)
                        if attachments:
                            event.attachments = attachments
                            logger.info(f"[HANDLER] Found {len(attachments)} attachments for issue {event.data.id}")
                    except Exception as e:
                        logger.exception(f"[HANDLER] Error getting attachments: {e}")

                return func(event)

            self.registered_handlers[event_name] = new_func
            return func

        return register_handler

    async def handle(self, event: dict) -> dict:
        """Handle incoming Linear events.

        Args:
            event: The event payload from Linear

        Returns:
            Response dictionary
        """
        logger.info("[HANDLER] Handling Linear event")

        try:
            # Extract event type
            event_type = event.get("type")
            if not event_type:
                logger.info("[HANDLER] No event type found in payload")
                return {"message": "Event type not found"}

            if event_type not in self.registered_handlers:
                logger.info(f"[HANDLER] No handler found for event type: {event_type}")
                return {"message": "Event handled successfully"}
            else:
                logger.info(f"[HANDLER] Handling event: {event_type}")
                handler = self.registered_handlers[event_type]
                result = handler(event)
                if hasattr(result, "__await__"):
                    result = await result
                return result

        except Exception as e:
            logger.exception(f"Error handling Linear event: {e}")
            return {"error": f"Failed to handle event: {e!s}"}

    def download_attachment(self, attachment: LinearAttachment, directory: Optional[str] = None) -> str:
        """Download a file attachment from Linear.

        Args:
            attachment: The LinearAttachment object
            directory: Optional directory to save the file to. If not provided, uses a temporary directory.

        Returns:
            Path to the downloaded file
        """
        try:
            # Download the attachment
            content = self.client.download_attachment(attachment.url)

            # Determine file path
            if directory:
                os.makedirs(directory, exist_ok=True)
                file_path = os.path.join(directory, attachment.title)
            else:
                # Create a temporary file
                temp_dir = tempfile.mkdtemp()
                file_path = os.path.join(temp_dir, attachment.title)

            # Write the file
            with open(file_path, "wb") as f:
                f.write(content)

            logger.info(f"[HANDLER] Downloaded attachment to {file_path}")
            return file_path
        except Exception as e:
            logger.exception(f"[HANDLER] Error downloading attachment: {e}")
            msg = f"Failed to download attachment: {e}"
            raise Exception(msg)

    def upload_file(self, file_path: str) -> str:
        """Upload a file to Linear.

        Args:
            file_path: Path to the file to upload

        Returns:
            URL of the uploaded file
        """
        return self.client.upload_file(file_path)
