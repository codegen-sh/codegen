import os
import json
import logging
import traceback
from typing import Dict, List, Any, Optional, Callable, Union

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse

from agentgen.extensions.events.interface import EventHandlerManagerProtocol
from agentgen.extensions.slack.types import SlackWebhookPayload
from agentgen.shared.logging.get_logger import get_logger

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
        logger.info("[HANDLER] Handling Slack event")

        try:
            event = SlackWebhookPayload.model_validate(event_data)

            if event.type == "url_verification":
                return {"challenge": event.challenge}
            elif event.type == "event_callback" and event.event:
                if event.event.type not in self.registered_handlers:
                    logger.info(f"[HANDLER] No handler found for event type: {event.event.type}")
                    return {"message": "Event handled successfully"}
                else:
                    handler = self.registered_handlers[event.event.type]
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
        logger.info(f"[EVENT] Registering handler for {event_name}")

        def register_handler(func):
            func_name = func.__qualname__
            logger.info(f"[EVENT] Registering function {func_name} for {event_name}")

            async def new_func(event):
                return await func(event)

            self.registered_handlers[event_name] = new_func
            return func

        return register_handler
