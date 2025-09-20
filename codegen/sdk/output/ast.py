from typing import Self

from openai import BaseModel
from pydantic.config import ConfigDict

from codegen.sdk.codebase.span import Span


class AST(BaseModel):
    model_config = ConfigDict(frozen=True)
    graph_sitter_type: str
    span: Span
    tree_sitter_type: str
    children: list[tuple[str | None, Self]]
