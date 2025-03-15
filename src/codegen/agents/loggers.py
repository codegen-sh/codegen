import json
from typing import Dict, List, Any, Union, Protocol
from dataclasses import asdict
from .data import BaseMessage

# Define the interface for ExternalLogger
class ExternalLogger(Protocol):
    """Protocol defining the interface for external loggers."""
    
    def log(self, data: Union[Dict[str, Any], BaseMessage]) -> None:
        """
        Log structured data to an external system.
        
        Args:
            data: The structured data to log, either as a dictionary or a BaseMessage
        """
        pass