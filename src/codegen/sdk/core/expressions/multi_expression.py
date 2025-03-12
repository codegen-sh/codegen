from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar, override

from codegen.sdk.core.expressions import Expression
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId


Parent = TypeVar("Parent", bound="Expression")
TExpression = TypeVar("TExpression", bound="Expression")


@apidoc
class MultiExpression(Expression[Parent], Generic[Parent, TExpression]):
    """Represents an group of Expressions, such as List, Dict, Binary Expression, String.

    Attributes:
        expressions: A list of expressions contained within the MultiExpression.
    """

    expressions: list[TExpression]

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, expressions: list[TExpression]) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self.expressions = expressions

    @noapidoc
    @commiter
    @override
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        for exp in self.expressions:
            exp._compute_dependencies(usage_type, dest)
