"""Base class for tool observations/responses."""

import json
from typing import Any, ClassVar, Optional

from pydantic import BaseModel, Field


class Observation(BaseModel):
    """Base class for all tool observations.

    All tool responses should inherit from this class to ensure consistent
    handling and string representations.
    """

    status: str = Field(
        default="success",
        description="Status of the operation - 'success' or 'error'",
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if status is 'error'",
    )

    # Class variable to store a template for string representation
    str_template: ClassVar[str] = "{status}: {details}"

    def _get_details(self) -> dict[str, Any]:
        """Get the details to include in string representation.

        Override this in subclasses to customize string output.
        By default, includes all fields except status and error.
        """
        return {k: v for k, v in self.model_dump().items() if k not in {"status", "error"} and v is not None}

    def __str__(self) -> str:
        """Get string representation of the observation."""
        if self.status == "error":
            return f"Error: {self.error}"

        details = self._get_details()
        if not details:
            return self.status

        return self.str_template.format(
            status=self.status,
            details=", ".join(f"{k}={v}" for k, v in details.items()),
        )

    def __repr__(self) -> str:
        """Get detailed string representation of the observation."""
        return f"{self.__class__.__name__}({self.model_dump_json()})"

    def render(self) -> str:
        """Render the observation as a string."""
        return json.dumps(self.model_dump(), indent=2)
