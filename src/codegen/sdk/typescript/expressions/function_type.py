from collections.abc import Generator
from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from tree_sitter import Node as TSNode

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.type import Type
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.typescript.detached_symbols.parameter import TSParameter
from codegen.sdk.typescript.placeholder.placeholder_return_type import TSReturnTypePlaceholder
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.typescript.expressions.type import TSType


Parent = TypeVar("Parent")


@ts_apidoc
class TSFunctionType(Type[Parent], Generic[Parent]):
    """Function type definition.

    Example:
        a: (a: number) => number

    Attributes:
        return_type: Return type of the function.
        name: This lets parameters generate their node_id properly.
    """

    return_type: "TSType[Self] | TSReturnTypePlaceholder[Self]"
    _parameters: Collection[TSParameter, Self]
    name: None = None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent):
        super().__init__(ts_node, file_node_id, ctx, parent)
        self.return_type = self.child_by_field_name("return_type", placeholder=TSReturnTypePlaceholder)
        params_node = self.ts_node.child_by_field_name("parameters")
        params = [TSParameter(child, idx, self) for idx, child in enumerate(params_node.named_children) if child.type != "comment"]
        self._parameters = Collection(params_node, file_node_id, ctx, self, children=params)

    @property
    @reader
    def parameters(self) -> Collection[TSParameter, Self]:
        """Retrieves the parameters of a function type.

        Returns the collection of parameters associated with this function type. These parameters represent the arguments that can be passed to the function.

        Returns:
            Collection[TSParameter, Self]: A collection of TSParameter objects representing the function's parameters.
        """
        return self._parameters

    @writer
    def asyncify(self) -> None:
        """Modifies the function type to be asynchronous by wrapping its return type in a Promise.

        This method transforms a synchronous function type into an asynchronous one by modifying
        its return type. It wraps the existing return type in a Promise, effectively changing
        'T' to 'Promise<T>'.

        Args:
            self: The TSFunctionType instance to modify.

        Returns:
            None
        """
        if self.return_type:
            self.return_type.insert_before("Promise<", newline=False)
            self.return_type.insert_after(">", newline=False)

    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: Importable | None = None):
        if self.return_type:
            self.return_type._compute_dependencies(UsageKind.GENERIC, dest)

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        yield from self.with_resolution_frame(self.return_type)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = []
        for param in self.parameters:
            symbols.extend(param.descendant_symbols)
        return symbols
