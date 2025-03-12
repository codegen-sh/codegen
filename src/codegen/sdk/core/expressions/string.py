from typing import TYPE_CHECKING, Generic, Self, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.builtin import Builtin
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


Parent = TypeVar("Parent", bound="Expression")


@apidoc
class String(Expression[Parent], Builtin, Generic[Parent]):
    """GraphSitter representation of String.

    Attributes:
        content: The content of the string
        content_nodes: A collection of string fragments and escape sequences in TS, or a single string content in Python.
        expressions: Embedded expressions in the string, only applicable for templated or formatted strings.
    """

    content: str
    content_nodes: Collection[Expression[Editable], Self]  # string content is a collection of string_fragments and escape_sequences in TS and a single string_content in Python
    expressions: list[Expression[Editable]]  # expressions in the string, only applicable for template strings

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        content_children = list(self.children_by_field_types({"string_content", "string_fragment", "escape_sequence"}))
        self.content_nodes = Collection(ts_node, self.file_node_id, self.ctx, self, delimiter="", children=content_children)
        self.content = "".join(x.ts_node.text.decode("utf-8") for x in content_children)

    @reader
    def __eq__(self, other: object) -> bool:
        if isinstance(other, str) and other == self.content:
            return True
        return super().__eq__(other)

    def __str__(self):
        return self.content

    def __hash__(self):
        return super().__hash__()

    @property
    @reader
    def with_quotes(self) -> str:
        """Retrieves the string representation with quotation marks.

        Returns:
            str: The string value with its surrounding quotation marks.
        """
        return self.source

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        # If the string is a template string, we need to compute the dependencies of the string content
        for expression in self.expressions:
            expression._compute_dependencies(usage_type, dest)

    @property
    def __class__(self):
        return str
