from __future__ import annotations

import itertools
from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from codegen.sdk.core.autocommit import writer
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.usable import Usable
from codegen.sdk.core.statements.assignment_statement import AssignmentStatement
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.extensions.autocommit import reader
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.assignment import Assignment
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.extensions.resolution import ResolutionStack

TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock | None")
TAssignment = TypeVar("TAssignment", bound="Assignment")


@apidoc
class Attribute(AssignmentStatement[TCodeBlock, TAssignment], Usable, Chainable, Generic[TCodeBlock, TAssignment]):
    """Abstract representation of an attribute on a class definition.

    Attributes:
        assignment: The assignment associated with the attribute.
    """

    statement_type = StatementType.CLASS_ATTRIBUTE
    assignment: TAssignment

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TCodeBlock, pos: int, assignment_node: TSNode) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos=pos, assignment_node=assignment_node)
        self.assignment = self.assignments[0]
        self._name_node = self.assignment.get_name()

    @abstractmethod
    def _get_name_node(self) -> TSNode:
        """Returns the ID node from the root node of the symbol."""

    @property
    @abstractmethod
    def is_private(self) -> bool:
        """Indicates whether the attribute is private.

        Determines if the attribute is a private class attribute by checking if it follows Python's private naming convention (i.e., starts with an underscore).

        Returns:
            bool: True if the attribute is private (starts with underscore), False otherwise.
        """
        ...

    @property
    @abstractmethod
    def is_optional(self) -> bool:
        """Returns whether the attribute is optional.

        Determines if an attribute's type annotation indicates it is optional/nullable. For example,
        if the attribute's type is `Optional[str]` or `str | None`, this will return True.

        Returns:
            bool: True if the attribute is marked as optional/nullable, False otherwise.
        """

    @writer
    def set_value(self, value: str) -> None:
        """Sets the value of a node's assignment.

        Updates the value of a node's assignment to the specified string value.

        Args:
            value (str): The new value to set for the assignment.

        Returns:
            None
        """
        self.assignment.set_value(value)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        return list(itertools.chain.from_iterable(assignment.descendant_symbols for assignment in self.assignments))

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        yield from self.with_resolution_frame(self.assignments[0])
