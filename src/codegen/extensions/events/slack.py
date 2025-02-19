import logging
import os
from typing import Literal

from pydantic import BaseModel, Field
from slack_sdk import WebClient

from codegen.extensions.events.interface import EventHandlerManagerProtocol

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class RichTextElement(BaseModel):
    type: str
    user_id: str | None = None
    text: str | None = None


class RichTextSection(BaseModel):
    type: Literal["rich_text_section"]
    elements: list[RichTextElement]


class Block(BaseModel):
    type: Literal["rich_text"]
    block_id: str
    elements: list[RichTextSection]


class SlackEvent(BaseModel):
    user: str
    type: str
    ts: str
    client_msg_id: str
    text: str
    team: str
    blocks: list[Block]
    channel: str
    event_ts: str


class SlackWebhookPayload(BaseModel):
    token: str | None = Field(None)
    team_id: str | None = Field(None)
    api_app_id: str | None = Field(None)
    event: SlackEvent | None = Field(None)
    type: str | None = Field(None)
    event_id: str | None = Field(None)
    event_time: int | None = Field(None)
    challenge: str | None = Field(None)
    subtype: str | None = Field(None)


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

    def handle(self, event: SlackWebhookPayload):
        logger.info("[HANDLER] Handling Slack event")
        if event.type == "url_verification":
            return {"challenge": event.challenge}
        elif event.type == "event_callback":
            event = event.event
            if event.type not in self.registered_handlers:
                logger.info(f"[HANDLER] No handler found for event type: {event.type}")
                return {"message": "Event handled successfully"}
            else:
                handler = self.registered_handlers[event.type]
                return handler(event)
        else:
            logger.info(f"[HANDLER] No handler found for event type: {event.type}")
            return {"message": "Event handled successfully"}

    def event(self, event_name: str):
        """Decorator for registering a Slack event handler."""
        logger.info(f"[EVENT] Registering handler for {event_name}")

        def register_handler(func):
            # Register the handler with the app's registry
            func_name = func.__qualname__
            logger.info(f"[EVENT] Registering function {func_name} for {event_name}")

            def new_func(event):
                return func(self.client, event)

            self.registered_handlers[event_name] = new_func
            return new_func

        return register_handler
