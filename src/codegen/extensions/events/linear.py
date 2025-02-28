import logging
from typing import Any, Callable, TypeVar

from pydantic import BaseModel

from codegen.extensions.events.interface import EventHandlerManagerProtocol
from codegen.extensions.linear.types import LinearEvent
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)

# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class Linear(EventHandlerManagerProtocol):
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}

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
