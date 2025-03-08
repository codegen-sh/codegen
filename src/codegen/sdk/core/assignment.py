from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from codegen.sdk._proxy import proxy_property
from codegen.sdk.core.autocommit import writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Expression, Name
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.core.expressions.multi_expression import MultiExpression
from codegen.sdk.core.expressions.subscript_expression import SubscriptExpression
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.typeable import Typeable
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.core.symbol_groups.dict import Dict
from codegen.sdk.enums import SymbolType
from codegen.sdk.extensions.autocommit import commiter, reader
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.typescript.expressions.object_type import TSObjectType
from codegen.sdk.utils import find_index
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.codebase.resolution_stack import ResolutionStack
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.assignment_statement import AssignmentStatement
    from codegen.sdk.core.statements.export_statement import ExportStatement
    from codegen.sdk.core.statements.statement import Statement

Parent = TypeVar("Parent", bound="AssignmentStatement | ExportStatement")


@apidoc
class Assignment(Symbol[Parent, ...], Typeable[Parent, ...], HasValue, Generic[Parent]):
    """Represents an assignment for a single variable within an assignment statement.

    Example:
        ```typescript
        var z
        var z = 5
        ```

    Attributes:
        symbol_type: The type of symbol, set to SymbolType.GlobalVar.
    """

    _left: Expression[Self]
    symbol_type = SymbolType.GlobalVar

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, left: TSNode, value: TSNode, name_node: TSNode, type: Type | None = None) -> None:
        self._unique_node = name_node  # HACK: This prevents deduplication of Assignments
        super().__init__(ts_node, file_node_id, ctx, parent=parent, name_node=name_node, name_node_type=Name)
        self._left = self._parse_expression(left, default=Name)
        self._value_node = self._parse_expression(value)
        self.type = type
        if self.type is None:
            self._init_type()

    @classmethod
    def _from_left_and_right_nodes(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, left_node: TSNode, right_node: TSNode) -> list[Assignment]:
        left = ctx.parser.parse_expression(left_node, file_node_id, ctx, parent)
        value = ctx.parser.parse_expression(right_node, file_node_id, ctx, parent)

        if isinstance(left, Collection | Dict):
            assignments = []
            for var in left.symbols:
                # Make a deep copy of the value expression for each child
                value = ctx.parser.parse_expression(right_node, file_node_id, ctx, parent)
                assignments.extend(cls._from_value_expression(ts_node, file_node_id, ctx, parent, left, value, var.ts_node))
            return sort_editables(assignments)
        return cls._from_value_expression(ts_node, file_node_id, ctx, parent, left, value, left_node)

    @classmethod
    def _from_value_expression(
        cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, left: Expression[Self], value: Expression[Self] | list[Expression], name_node: TSNode
    ) -> list[Assignment]:
        assignments = [cls(ts_node, file_node_id, ctx, parent, left, value, name_node)]
        if value and isinstance(value, MultiExpression) and isinstance(value.expressions[0], Assignment):
            for expr in value.expressions:
                assignments.extend(cls._from_value_expression(expr.ts_node, file_node_id, ctx, parent, expr.left, expr.value, expr.get_name().ts_node))
        return sort_editables(assignments)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        dest = self.self_dest
        if value := self.value:
            value._compute_dependencies(UsageKind.BODY, dest)
        if self.type:
            self.type._compute_dependencies(UsageKind.TYPE_ANNOTATION, dest)

        # Check for usages in left hand side of assignment if it is an object access
        if name := self.get_name():
            if isinstance(name, ChainedAttribute):
                name._compute_dependencies(UsageKind.BODY, dest)
            elif isinstance(name, SubscriptExpression):
                name._compute_dependencies(UsageKind.BODY, dest)

    @property
    @noapidoc
    @reader
    def left(self) -> Expression[Self]:
        """The left side of the assignment.

        Only should be used for internal purposes.
        """
        return self._left

    @property
    @reader
    def index(self) -> int:
        """Returns the index of the assignment statement in its parent's code block.

        Returns:
            int: The 0-based index position of the assignment statement within its parent's code block statements.
        """
        return self.parent.index

    @property
    @reader
    def is_local_variable(self) -> bool:
        """Determines if an assignment represents a local variable in the current scope.

        A local variable is an assignment that:
        1. Is not a chained attribute (e.g., not self.x or obj.x)
        2. Is not in the global (file) scope

        Returns:
            bool: True if the assignment is a local variable, False otherwise.
        """
        from codegen.sdk.core.file import File

        if isinstance(self._left, ChainedAttribute):
            return False

        if isinstance(self.parent, File):
            return False
        return True

    @proxy_property
    @reader
    def local_usages(self) -> list[Editable[Statement]]:
        """Retrieves all usages of the assigned variable within its code block scope.

        Returns all instances where the variable defined in this Assignment is used within its code block. Only returns usages that occur after the assignment, excluding the usage in the assignment
        itself.

        Returns:
            list[Editable[Statement]]: A sorted list of statement nodes where the variable is used.

        Note:
            This method can be called as both a property or a method. If used as a property, it is equivalent to invoking it without arguments.
        """
        usages = []
        for statement in self.parent.parent.statements[self.index :]:
            var_references = statement.get_variable_usages(self.name)
            for var_reference in var_references:
                # Exclude the variable usage in the assignment itself
                if self.ts_node.byte_range[0] <= var_reference.ts_node.start_byte and self.ts_node.byte_range[1] >= var_reference.ts_node.end_byte:
                    continue
                usages.append(var_reference)
        return sort_editables(usages)

    @writer
    def set_value(self, src: str) -> None:
        """Sets the value of an assignment expression.

        Updates the value of an assignment expression. If the assignment doesn't have an existing value,
        it adds one after the type annotation (if present) or after the variable name. If the assignment
        already has a value, it replaces the existing value.

        Args:
            src (str): The source code string representing the new value to be assigned.

        Returns:
            None
        """
        if self.value is None:
            if self.type:
                self.type.insert_after(f" = {src}", newline=False)
            else:
                self.insert_after(f" = {src}", newline=False)
        else:
            self.value.edit(src)

    @writer
    def set_type_annotation(self, type_str: str) -> None:
        """Adds or updates a type annotation for the current assignment.

        This method modifies an assignment statement to include a type annotation. If the assignment already
        has a type annotation, it will be overwritten with the new type. If no type annotation exists,
        one will be added between the assignment name and the equals sign.

        Args:
            type_str (str): The type annotation to be added or updated.

        Returns:
            None
        """
        type_annotation_node = self.type
        if type_annotation_node:
            type_annotation_node.edit(type_str)
        else:
            self._left.insert_after(f": {type_str}", newline=False)

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        if isinstance(self.type, Chainable) and not self.type.source == "TypeAlias":
            yield from self.with_resolution_frame(self.type, direct=False)
        elif self.value:
            resolved = False
            from codegen.sdk.core.statements.assignment_statement import AssignmentStatement

            if self.parent_of_type(AssignmentStatement) and len(self.parent_of_type(AssignmentStatement).assignments) > 0:
                name_node = self._name_node.ts_node
                if name_node and (val := self.value) and isinstance(val, Chainable):
                    for resolution in val.resolved_type_frames:
                        type = resolution.top.node
                        current = self.ts_node
                        while current and current.id != name_node.id:
                            idx = find_index(name_node, current.named_children)
                            current = current.named_children[idx] if idx != -1 else None
                            if current is None:
                                break
                            if current.type == "object_pattern":
                                if name_node in current.named_children:
                                    if isinstance(type, TSObjectType):
                                        type = type.get(self.name)
                                        current = name_node
                            if current.type == "pair_pattern":
                                key = current.child_by_field_name("key")
                                if isinstance(type, TSObjectType) and (elem := type.get(key.text.decode("utf-8"))):
                                    type = elem

                        if type and type != resolution.top.node:
                            yield from self.with_resolution_frame(type, direct=False, chained=True)
                            resolved = True
            if not resolved:
                yield from self.with_resolution_frame(self.value, direct=False)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = super().descendant_symbols
        if self.type:
            symbols.extend(self.type.descendant_symbols)
        if self.value is not None:
            symbols.extend(self.value.descendant_symbols)
        return symbols

    def __hash__(self):
        if self._hash is None:
            self._hash = hash((self.filepath, self.range, self.ts_node.kind_id, self._unique_node.range))
        return self._hash

    @reader
    def __eq__(self, other: object):
        if isinstance(other, Assignment):
            return super().__eq__(other) and self._unique_node.range == other._unique_node.range
        return super().__eq__(other)

    @writer
    def reduce_condition(self, bool_condition: bool, node: Editable | None = None) -> None:
        """Simplifies an assignment expression by reducing it based on a boolean condition and updating all the usages.


        Args:
            bool_condition (bool): The boolean value to reduce the condition to.

        """
        self.remove()
        for usage in self.usages:
            if usage.match == self.name:
                usage.match.reduce_condition(bool_condition)
