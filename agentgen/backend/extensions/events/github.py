import logging
import os
from typing import Any, Callable, TypeVar

from fastapi import Request
from github import Github
from pydantic import BaseModel

from codegen.extensions.events.interface import EventHandlerManagerProtocol
from codegen.extensions.github.types.base import GitHubInstallation, GitHubWebhookPayload
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
logger.setLevel(logging.DEBUG)


# Type variable for event types
T = TypeVar("T", bound=BaseModel)


class GitHub(EventHandlerManagerProtocol):
    def __init__(self, app):
        self.app = app
        self.registered_handlers = {}

    @property
    def client(self) -> Github:
        if not os.getenv("GITHUB_TOKEN"):
            msg = "GITHUB_TOKEN is not set"
            logger.exception(msg)
            raise ValueError(msg)
        if not self._client:
            self._client = Github(os.getenv("GITHUB_TOKEN"))
        return self._client

    def unsubscribe_all_handlers(self):
        logger.info("[HANDLERS] Clearing all handlers")
        self.registered_handlers.clear()

    def event(self, event_name: str):
        """Decorator for registering a GitHub event handler.

        Example:
            @app.github.event('push')
            def handle_push(event: PushEvent):  # Can be typed with Pydantic model
                logger.info(f"Received push to {event.ref}")

            @app.github.event('pull_request:opened')
            def handle_pr(event: dict):  # Or just use dict for raw event
                logger.info(f"Received PR")
        """
        logger.info(f"[EVENT] Registering handler for {event_name}")

        def register_handler(func: Callable[[T], Any]):
            # Get the type annotation from the first parameter
            event_type = func.__annotations__.get("event")
            func_name = func.__qualname__
            logger.info(f"[EVENT] Registering function {func_name} for {event_name}")

            def new_func(raw_event: dict):
                # Only validate if a Pydantic model was specified
                if event_type and issubclass(event_type, BaseModel):
                    try:
                        parsed_event = event_type.model_validate(raw_event)
                        return func(parsed_event)
                    except Exception as e:
                        logger.exception(f"Error parsing event: {e}")
                        raise
                else:
                    # Pass through raw dict if no type validation needed
                    return func(raw_event)

            self.registered_handlers[event_name] = new_func
            return new_func

        return register_handler

    async def handle(self, event: dict, request: Request | None = None) -> dict:
        """Handle both webhook events and installation callbacks."""
        logger.info("[HANDLER] Handling GitHub event")

        # Check if this is an installation event
        if "installation_id" in event and "code" in event:
            installation = GitHubInstallation.model_validate(event)
            logger.info("=====[GITHUB APP INSTALLATION]=====")
            logger.info(f"Code: {installation.code}")
            logger.info(f"Installation ID: {installation.installation_id}")
            logger.info(f"Setup Action: {installation.setup_action}")
            return {
                "message": "GitHub app installation details received",
                "details": {
                    "code": installation.code,
                    "installation_id": installation.installation_id,
                    "setup_action": installation.setup_action,
                },
            }

        # Extract headers for webhook events if request is provided
        headers = {}
        if request:
            headers = {
                "x-github-event": request.headers.get("x-github-event"),
                "x-github-delivery": request.headers.get("x-github-delivery"),
                "x-github-hook-id": request.headers.get("x-github-hook-id"),
                "x-github-hook-installation-target-id": request.headers.get("x-github-hook-installation-target-id"),
                "x-github-hook-installation-target-type": request.headers.get("x-github-hook-installation-target-type"),
            }

        # Handle webhook events
        try:
            # For simulation, use event data directly
            if not request:
                event_type = f"pull_request:{event['action']}" if "action" in event else event.get("type", "unknown")
                if event_type not in self.registered_handlers:
                    logger.info(f"[HANDLER] No handler found for event type: {event_type}")
                    return {"message": "Event type not handled"}
                else:
                    logger.info(f"[HANDLER] Handling event: {event_type}")
                    handler = self.registered_handlers[event_type]
                    return handler(event)

            # For actual webhooks, use the full payload
            webhook = GitHubWebhookPayload.model_validate({"headers": headers, "event": event})
            event_type = webhook.headers.event_type
            action = webhook.event.action
            full_event_type = f"{event_type}:{action}" if action else event_type

            if full_event_type not in self.registered_handlers:
                logger.info(f"[HANDLER] No handler found for event type: {full_event_type}")
                return {"message": "Event type not handled"}
            else:
                logger.info(f"[HANDLER] Handling event: {full_event_type}")
                handler = self.registered_handlers[full_event_type]
                return handler(event)

        except Exception as e:
            logger.exception(f"Error handling webhook: {e}")
            raise
