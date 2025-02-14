import functools
import logging
import os
from typing import Callable

import modal  # deptry: ignore
from anthropic import BaseModel

from codegen.extensions.clients.linear import LinearClient
from codegen.extensions.events.interface import EventHandlerManagerProtocol

logger = logging.getLogger(__name__)


class RegisteredWebhookHandler(BaseModel):
    webhook_id: str | None = None
    handler_func: Callable


class Linear(EventHandlerManagerProtocol):
    def __init__(self, app: modal.App):
        self.app = app
        self.access_token = os.environ["LINEAR_ACCESS_TOKEN"]  # move to extensions config.
        self.signing_secret = os.environ["LINEAR_SIGNING_SECRET"]
        self.linear_team_id = os.environ["LINEAR_TEAM_ID"]
        self.registered_handlers = {}

    def subscribe_handler_to_webhook(self, web_url: str, event_name: str):
        client = LinearClient(access_token=self.access_token)

        result = client.register_webhook(team_id=self.linear_team_id, webhook_url=web_url, enabled=True, resource_types=[event_name], secret=self.signing_secret)
        return result

    def unsubscribe_handler_to_webhook(self, registered_handler: RegisteredWebhookHandler):
        webhook_id = registered_handler.webhook_id

        client = LinearClient(access_token=self.access_token)
        if webhook_id:
            print(f"Unsubscribing from webhook {webhook_id}")
            result = client.unregister_webhook(webhook_id)
            return result
        else:
            print("No webhook id found for handler")
            return None

    def unsubscribe_all_handlers(self):
        for handler in self.registered_handlers:
            self.unsubscribe_handler_to_webhook(self.registered_handlers[handler])

    def event(self, event_name):
        """Decorator for registering an event handler.

        :param event_name: The name of the event to handle.
        :param register_hook: An optional function to call during registration,
                              e.g., to make an API call to register the webhook.
        """

        def decorator(func):
            # Register the handler with the app's registry.
            modal_ready_func = func
            func_name = func.__qualname__
            app_name = self.app.name
            web_url = modal.Function.from_name(app_name=app_name, name=func_name).web_url

            self.registered_handlers[func_name] = RegisteredWebhookHandler(handler_func=modal_ready_func)

            webhook_id = self.subscribe_handler_to_webhook(web_url=web_url, event_name=event_name)
            self.registered_handlers[func_name].webhook_id = webhook_id

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorator
