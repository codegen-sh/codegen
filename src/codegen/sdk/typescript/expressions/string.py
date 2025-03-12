from typing import TYPE_CHECKING, Generic, TypeVar

from tree_sitter import Node as TSNode

from codegen.sdk.core.expressions import Expression, String
from codegen.sdk.core.node_id_factory import NodeId
from codegen.shared.decorators.docs import ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.codebase.codebase_context import CodebaseContext


Parent = TypeVar("Parent", bound="Expression")


@ts_apidoc
class TSString(String, Generic[Parent]):
    """A TypeScript string node representing both literal strings and template strings.

    This class handles both regular string literals and template strings in TypeScript,
    providing functionality to parse and manage template string expressions. It extends
    the base String class with TypeScript-specific capabilities.

    Attributes:
        expressions (list): A list of parsed expressions from template string substitutions.
            Empty for regular string literals.
    """

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: "CodebaseContext", parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        if ts_node.type == "template_string":
            substitutions = [x for x in ts_node.named_children if x.type == "template_substitution"]
            self.expressions = [self._parse_expression(x.named_children[0]) for x in substitutions]
        else:
            self.expressions = []
