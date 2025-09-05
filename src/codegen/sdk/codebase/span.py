from typing import Annotated, Any

from pydantic import BaseModel
from pydantic.config import ConfigDict
from pydantic.functional_validators import BeforeValidator
from pydantic.json_schema import JsonSchemaValue, WithJsonSchema
from pydantic_core.core_schema import ValidationInfo
from tree_sitter import Point, Range

from codegen.sdk.shared.decorators.docs import apidoc


def validate_range(value: Any, info: ValidationInfo) -> Range:
    if isinstance(value, dict):
        value = Range(
            start_byte=value["start_byte"],
            end_byte=value["end_byte"],
            start_point=Point(**value["start_point"]),
            end_point=Point(**value["end_point"]),
        )
    elif not isinstance(value, Range):
        msg = "Invalid type for range field. Expected tree_sitter.Range or dict."
        raise ValueError(msg)
    return value


def range_json_schema() -> JsonSchemaValue:
    return {
        "type": "object",
        "properties": {
            "start_byte": {"type": "integer"},
            "end_byte": {"type": "integer"},
            "start_point": {
                "type": "object",
                "properties": {
                    "row": {"type": "integer"},
                    "column": {"type": "integer"},
                },
            },
            "end_point": {
                "type": "object",
                "properties": {"row": {"type": "integer"}, "column": {"type": "integer"}},
            },
        },
    }


RangeAdapter = Annotated[
    Range,
    BeforeValidator(validate_range),
    WithJsonSchema(range_json_schema()),
]


@apidoc
class Span(BaseModel):
    """Range within the codebase

    Attributes:
        range: Adapter for the range within the codebase.
        filepath: The path to the file associated with the range.
    """

    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        json_encoders={
            Range: lambda r: {
                "start_byte": r.start_byte,
                "end_byte": r.end_byte,
                "start_point": {
                    "row": r.start_point.row,
                    "column": r.start_point.column,
                },
                "end_point": {
                    "row": r.end_point.row,
                    "column": r.end_point.column,
                },
            }
        },
    )
    range: RangeAdapter
    filepath: str
