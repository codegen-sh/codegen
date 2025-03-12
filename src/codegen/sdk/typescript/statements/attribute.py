from __future__ import annotations

from typing import TYPE_CHECKING

from codegen.sdk._proxy import proxy_property
from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.statements.attribute import Attribute
from codegen.sdk.typescript.assignment import TSAssignment
from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
from codegen.sdk.typescript.statements.assignment_statement import TSAssignmentStatement
from codegen.shared.decorators.docs import ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.interfaces.has_block import TSHasBlock


@ts_apidoc
class TSAttribute(Attribute[TSCodeBlock, TSAssignment], TSAssignmentStatement):
    """Typescript implementation of Attribute detached symbol."""

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: TSCodeBlock, pos: int) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent, pos=pos, assignment_node=ts_node)
        self.type = self.assignments[0].type

    @reader
    def _get_name_node(self) -> TSNode:
        """Returns the ID node from the root node of the symbol"""
        return self.ts_node.child_by_field_name("name")

    @proxy_property
    @reader
    def local_usages(self: TSAttribute[TSHasBlock, TSCodeBlock]) -> list[Editable]:
        """Returns local usages of a TypeScript attribute within its code block.

        Searches through all statements in the attribute's parent code block and finds instances where the attribute is referenced with 'this.' prefix. Excludes the attribute's own
        declaration/assignment.

        Args:
            self (TSAttribute[TSHasBlock, TSCodeBlock]): The TypeScript attribute instance.

        Returns:
            list[Editable]: A sorted list of unique Editable instances representing local usages of the attribute, ordered by their position in the source code.

        Note:
            This method can be called as both a property or a method. If used as a property, it is equivalent to invoking it without arguments.
        """
        usages = []
        for statement in self.parent.statements:
            var_references = statement.find(f"this.{self.name}", exact=True)
            for var_reference in var_references:
                # Exclude the variable usage in the assignment itself
                if self.ts_node.byte_range[0] <= var_reference.ts_node.start_byte and self.ts_node.byte_range[1] >= var_reference.ts_node.end_byte:
                    continue
                usages.append(var_reference)
        return sorted(dict.fromkeys(usages), key=lambda x: x.ts_node.start_byte)

    @property
    def is_private(self) -> bool:
        """Determines if this attribute has a private accessibility modifier.

        Args:
            self: The TypeScript attribute instance.

        Returns:
            bool: True if the attribute has a 'private' accessibility modifier, False otherwise.
        """
        modifier = self.ts_node.children[0]
        return modifier.type == "accessibility_modifier" and modifier.text == b"private"

    @property
    def is_optional(self) -> bool:
        """Returns True if this attribute is marked as optional in TypeScript.

        Checks if the attribute has a question mark (`?`) symbol after its name, indicating it's an optional field.

        Returns:
            bool: True if the attribute is optional, False otherwise.
        """
        if sibling := self.get_name().next_sibling:
            return sibling.ts_node.type == "?"
        return False
