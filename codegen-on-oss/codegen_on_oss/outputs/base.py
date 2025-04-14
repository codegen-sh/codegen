import json
from typing import Any

from loguru import logger


class BaseOutput:
    """
    BaseOutput is a class that defines the interface for all output classes.
    """

    def __init__(self, fields: list[str]):
        self.fields = fields

    def write_output(self, value: dict[str, Any]):
        logger.info(json.dumps(value, indent=4))
