from typing import Protocol

from .data import AgentRunMessage


# Define the interface for ExternalLogger
class ExternalLogger(Protocol):
    """Protocol defining the interface for external loggers."""

    def log(self, data: AgentRunMessage) -> None:
        """Log structured data to an external system.

        Args:
            data: The structured data to log, either as a dictionary or a BaseMessage
        """
        pass
