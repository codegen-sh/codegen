from typing import Any, Self

from pydantic import BaseModel


class SafeBaseModel(BaseModel):
    @classmethod
    def model_validate(
        cls, obj: Any, *, strict: bool | None = None, from_attributes: bool | None = None, context: Any | None = None, by_alias: bool | None = None, by_name: bool | None = None
    ) -> "Self":
        try:
            return super().model_validate(obj, strict=strict, from_attributes=from_attributes, context=context, by_alias=by_alias, by_name=by_name)
        except Exception as e:
            print(e)
            # Return a default instance instead of None to maintain compatibility
            return cls()

    def __str__(self) -> str:
        return self.model_dump_json(indent=4)


class CodemodConfig(BaseModel):
    """Configuration for a codemod."""

    name: str
    codemod_id: int
    description: str | None = None
    created_at: str
    created_by: str
