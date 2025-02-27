import logging
import os

from slack_sdk import WebClient

from codegen.extensions.events.interface import EventHandlerManagerProtocol
from codegen.extensions.slack.types import SlackWebhookPayload
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


class Slack(EventHandlerManagerProtocol):
    _client: WebClient | None = None

    def __init__(self, app):
        self.registered_handlers = {}

    @property
    def client(self) -> WebClient:
        if not self._client:
            self._client = WebClient(token=os.environ["SLACK_BOT_TOKEN"])
        return self._client

    def unsubscribe_all_handlers(self):
        logger.info("[HANDLERS] Clearing all handlers")
        self.registered_handlers.clear()

    async def handle(self, event_data: dict) -> dict:
        """Handle incoming Slack events."""
        logger.info("[HANDLER] Handling Slack event")

        try:
            # Validate and convert to SlackWebhookPayload
            event = SlackWebhookPayload.model_validate(event_data)

            if event.type == "url_verification":
                return {"challenge": event.challenge}
            elif event.type == "event_callback" and event.event:
                if event.event.type not in self.registered_handlers:
                    logger.info(f"[HANDLER] No handler found for event type: {event.event.type}")
                    return {"message": "Event handled successfully"}
                else:
                    handler = self.registered_handlers[event.event.type]
                    # Since the handler might be async, await it
                    result = handler(event.event)
                    if hasattr(result, "__await__"):
                        result = await result
                    return result
            else:
                logger.info(f"[HANDLER] No handler found for event type: {event.type}")
                return {"message": "Event handled successfully"}

        except Exception as e:
            logger.exception(f"Error handling Slack event: {e}")
            return {"error": f"Failed to handle event: {e!s}"}

    def event(self, event_name: str):
        """Decorator for registering a Slack event handler."""
        logger.info(f"[EVENT] Registering handler for {event_name}")

        def register_handler(func):
            # Register the handler with the app's registry
            func_name = func.__qualname__
            logger.info(f"[EVENT] Registering function {func_name} for {event_name}")

            async def new_func(event):
                # Just pass the event, handler can access client via app.slack.client
                return await func(event)

            self.registered_handlers[event_name] = new_func
            return func

        return register_handler
