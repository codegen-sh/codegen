from typing import Protocol

import modal  # deptry: ignore


class EventHandlerManagerProtocol(Protocol):
    def subscribe_handler_to_webhook(self, func_name: str, modal_app: modal.App, event_name):
        pass

    def unsubscribe_handler_to_webhook(self, func_name: str, modal_app: modal.App, event_name):
        pass

    def unsubscribe_all_handlers(self):
        pass
