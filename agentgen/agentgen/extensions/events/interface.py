from typing import Protocol


class EventHandlerManagerProtocol(Protocol):
    def event(self, event_name: str):
        """Decorator for registering an event handler."""
        pass

    def unsubscribe_all_handlers(self):
        """Unsubscribe all event handlers."""
        pass
