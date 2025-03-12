from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, override

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.expressions.multi_expression import MultiExpression
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.detached_symbols.parameter import Parameter
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId


Parent = TypeVar("Parent", bound="FunctionCall")
TParameter = TypeVar("TParameter", bound="Parameter")


@apidoc
class Argument(Expression[Parent], HasName, HasValue, Generic[Parent, TParameter]):
    """Represents an argument passed into a FunctionCall."""

    _pos: int

    def __init__(self, node: TSNode, positional_idx: int, parent: FunctionCall) -> None:
        super().__init__(node, parent.file_node_id, parent.ctx, parent)
        self._pos = positional_idx

        # TODO: Make the python and typescript implementations into different classes
        # Python
        if node.type == "keyword_argument":
            name_node = node.child_by_field_name("name")
            _value_node = node.child_by_field_name("value")
        # TypeScript
        elif node.type == "assignment_expression":
            name_node = node.child_by_field_name("left")
            _value_node = node.child_by_field_name("right")
        else:
            name_node = None
            _value_node = node

        self._name_node = self._parse_expression(name_node, default=Name)
        self._value_node = self._parse_expression(_value_node)

    def __repr__(self) -> str:
        keyword = f"keyword={self.name}, " if self.name else ""
        value = f"value='{self.value}', " if self.value else ""
        type = f"type={self.type}" if self.type else ""

        return f"Argument({keyword}{value}{type})"

    @noapidoc
    @classmethod
    def from_argument_list(cls, node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: FunctionCall) -> MultiExpression[Parent, Argument]:
        args = [Argument(x, file_node_id, ctx, parent, i) for i, x in enumerate(node.named_children) if x.type != "comment"]
        return MultiExpression(node, file_node_id, ctx, parent, expressions=args)

    @property
    @reader
    def index(self) -> int:
        """Returns the zero-based index of this argument within its parent function call.

        Args:
            None

        Returns:
            int: The zero-based position of this argument in the function call's argument list.
        """
        return self._pos

    @property
    @reader
    def type(self) -> str:
        """Gets the `Tree-sitter` type of the argument's value node.

        Returns the type string of the underlying TreeSitter node that represents this argument's value.
        This can be useful for checking if the argument is a specific type of expression or literal.

        Returns:
            str: The TreeSitter node type of the argument's value.
        """
        return self._value_node.ts_node.type

    @property
    @reader
    def is_named(self) -> bool:
        """Determines if an argument is being passed as a named keyword argument.

        Args:
            None

        Returns:
            bool: True if the argument is being passed with a name (e.g., param=value), False if it's a positional argument.
        """
        return self.name is not None

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def add_keyword(self, keyword: str) -> None:
        """Converts an unnamed argument to a named argument by adding a keyword.

        Adds the specified keyword to an unnamed argument in a function call, making it a named argument.
        For example, turning a positional argument 'value' into a named argument 'param=value'.

        Args:
            keyword (str): The keyword name to be added to the argument.

        Raises:
            ValueError: If the argument is already a named argument.
        """
        if self.is_named:
            msg = f"Argument {self.source} already has a keyword argument at file {self.file_node_id}"
            raise ValueError(msg)

        self.insert_before(f"{keyword}=", newline=False)

    @noapidoc
    @commiter
    @override
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        if value := self.value:
            value._compute_dependencies(usage_type, dest)

    @property
    @reader
    @noapidoc
    def parameter(self) -> TParameter | None:
        """Provides access to the corresponding Parameter (defined on the Function being called) for this argument."""
        if self.is_named:
            return self.parent.find_parameter_by_name(self.name)
        return self.parent.find_parameter_by_index(self.index)

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns a list of function calls present in the value of this argument.

        Retrieves all function call nodes that are present within the value of this argument. This is useful for call graph analysis and tracking function usage within arguments.

        Returns:
            list[FunctionCall]: A list containing all function calls within the argument's value.
        """
        return self.value.function_calls

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        if self.value:
            return self.value.descendant_symbols
        return []
