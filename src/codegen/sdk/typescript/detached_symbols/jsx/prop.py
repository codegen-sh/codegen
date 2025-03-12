from typing import TYPE_CHECKING, override

from tree_sitter import Node as TSNode

from codegen.sdk.codebase.codebase_context import CodebaseContext
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.extensions.autocommit import commiter
from codegen.sdk.typescript.detached_symbols.jsx.expression import JSXExpression
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.function import Function
    from codegen.sdk.typescript.detached_symbols.jsx.element import JSXElement


@ts_apidoc
class JSXProp(Expression["Function | JSXElement | JSXProp"], HasName, HasValue):
    """Abstract representation of TSX/JSX prop, e.g <Component prop="value" />."""

    _name_node: Name | None
    _expression_node: JSXExpression | None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: "Function | JSXElement | JSXProp") -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self._name_node = self._parse_expression(self.ts_node.children[0], default=Name)
        if len(self.ts_node.children) > 2:
            self._value_node = self._parse_expression(self.ts_node.children[2])
            if self._value_node.ts_node.type == "jsx_expression":
                self._expression_node = self._parse_expression(self._value_node.ts_node)
            else:
                self._expression_node = None
        else:
            # If there is no value node, then the prop is a boolean prop
            # For example, <Component prop /> is equivalent to <Component prop={true} />
            self._value_node = None

    @property
    @reader
    def expression(self) -> JSXExpression | None:
        """Retrieves the JSX expression associated with this JSX prop.

        Returns the JSX expression node if this prop has one, e.g., for props like prop={expression}.
        For boolean props or string literal props, returns None.

        Returns:
            JSXExpression | None: The JSX expression node if present, None otherwise.
        """
        return self._expression_node

    @writer
    def insert_after(
        self,
        new_src: str,
        fix_indentation: bool = False,
        newline: bool = True,
        priority: int = 0,
        dedupe: bool = True,
    ) -> None:
        """Inserts source code after a JSX prop in a TypeScript/JSX file.

        Inserts the provided source code after the current JSX prop, adding necessary spacing.

        Args:
            new_src (str): The source code to insert after the prop.
            fix_indentation (bool, optional): Whether to fix the indentation of the inserted code. Defaults to False.
            newline (bool, optional): Whether to add a newline after the inserted code. Defaults to True.
            priority (int, optional): The priority of the insertion. Defaults to 0.
            dedupe (bool, optional): Whether to prevent duplicate insertions. Defaults to True.

        Returns:
            None
        """
        # TODO: This may not be transaction save with adds and deletes
        # Insert space after the prop name
        super().insert_after(" " + new_src, fix_indentation, newline, priority, dedupe)

    @writer
    def insert_before(
        self,
        new_src: str,
        fix_indentation: bool = False,
        newline: bool = True,
        priority: int = 0,
        dedupe: bool = True,
    ) -> None:
        """Insert a new source code string before a JSX prop in a React component.

        Inserts a new string of source code before a JSX prop, maintaining proper spacing.
        Automatically adds a trailing space after the inserted code.

        Args:
            new_src (str): The source code string to insert before the prop.
            fix_indentation (bool, optional): Whether to adjust the indentation of the inserted code. Defaults to False.
            newline (bool, optional): Whether to add a newline after the inserted code. Defaults to True.
            priority (int, optional): Priority of this insertion relative to others. Defaults to 0.
            dedupe (bool, optional): Whether to avoid duplicate insertions. Defaults to True.

        Returns:
            None
        """
        # TODO: This may not be transaction save with adds and deletes
        # Insert space before the prop name
        super().insert_before(new_src + " ", fix_indentation, newline, priority, dedupe)

    @commiter
    @noapidoc
    @override
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        for node in self.children:
            node._compute_dependencies(usage_type, dest=dest)
