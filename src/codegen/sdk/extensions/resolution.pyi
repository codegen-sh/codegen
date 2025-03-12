from dataclasses import dataclass, field
from functools import cached_property as cached_property
from typing import Generic

from typing_extensions import TypeVar

from codegen.sdk.codebase.codebase_context import CodebaseContext
from codegen.sdk.core.dataclasses.usage import UsageKind, UsageType
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_name import HasName

NodeType = TypeVar("NodeType")

@dataclass
class ResolutionStack(Generic[NodeType]):
    """Represents the resolution stack from a symbol to a usage

    Symbol
    ...
    <Imports, Assignments, Etc>

    Attributes:
        aliased: If this was aliased at any point
        parent_frame: The frame above this frame
    """

    node: NodeType = ...
    parent_frame: ResolutionStack | None = ...
    direct: bool = True
    aliased: bool = False
    chained: bool = False
    generics: dict = field(default_factory=dict)

    def with_frame(self, node, direct: bool = True, aliased: bool = False, chained: bool = False, generics: dict | None = None) -> ResolutionStack:
        """Adds node to the Resolution stack and returns it as a new frame."""
        ...

    def usage_type(self, direct: bool, aliased: bool) -> UsageType: ...
    def add_usage(self, match: Editable, usage_type: UsageKind, dest: HasName, codebase_context: CodebaseContext, *, direct: bool = True, aliased: bool = False, chained: bool = False) -> None:
        """Add the resolved type to the graph. Also adds any intermediate nodes as usages as well if they are on the graph."""

    @cached_property
    def top(self) -> ResolutionStack: ...
    @cached_property
    def is_direct_usage(self) -> bool: ...
    def with_new_base(self, base, *args, **kwargs) -> ResolutionStack: ...
    def with_new_base_frame(self, base: ResolutionStack) -> ResolutionStack: ...
    def __init__(self, node, parent_frame=..., aliased=..., direct=..., _seen=...) -> None: ...
