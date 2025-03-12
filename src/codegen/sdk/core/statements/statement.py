from __future__ import annotations

from enum import StrEnum
from functools import cached_property
from typing import TYPE_CHECKING, Generic, Self, TypeVar, final

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.expressions import Expression
from codegen.sdk.extensions.autocommit import commiter
from codegen.sdk.output.constants import ANGULAR_STYLE
from codegen.sdk.utils import find_all_descendants
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    import rich.repr
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection


@apidoc
class StatementType(StrEnum):
    """Enum representing the different types of statements that can be parsed.

    Attributes:
        COMMENT: Represents a comment statement.
        ASSIGNMENT: Represents an assignment expression.
        EXPRESSION_STATEMENT: Represents an expression statement.
        CLASS_ATTRIBUTE: Represents a class attribute.
        RETURN_STATEMENT: Represents a return statement.
        RAISE_STATEMENT: Represents a raise statement.
        WITH_STATEMENT: Represents a with statement.
        PASS_STATEMENT: Represents a pass statement.
        BREAK_STATEMENT: Represents a break statement.
        LABELED_STATEMENT: Represents a labeled statement.
        TRY_CATCH_STATEMENT: Represents a try-catch statement.
        IF_BLOCK_STATEMENT: Represents an if block statement.
        FOR_LOOP_STATEMENT: Represents a for loop statement.
        WHILE_STATEMENT: Represents a while statement.
        SWITCH_STATEMENT: Represents a switch statement.
        SYMBOL_STATEMENT: Represents a symbol statement.
        UNSPECIFIED: Represents any unparsed code snippet or graph node statements.
        EXPORT_STATEMENT: Represents an export statement.
        IMPORT_STATEMENT: Represents an import statement.
    """

    COMMENT = "comment"
    ASSIGNMENT = "assignment_expression"
    EXPRESSION_STATEMENT = "expression_statement"
    CLASS_ATTRIBUTE = "class_attribute"
    RETURN_STATEMENT = "return_statement"
    RAISE_STATEMENT = "raise_statement"
    WITH_STATEMENT = "with_statement"
    PASS_STATEMENT = "pass_statement"
    BREAK_STATEMENT = "pass_statement"
    LABELED_STATEMENT = "labeled_statement"
    TRY_CATCH_STATEMENT = "try_catch_statement"
    IF_BLOCK_STATEMENT = "if_block_statement"
    FOR_LOOP_STATEMENT = "for_loop_statement"
    WHILE_STATEMENT = "while_statement"
    SWITCH_STATEMENT = "switch_statement"
    SYMBOL_STATEMENT = "symbol_statement"
    # Any unparsed code snippet, or graph node statements (e.g. function definition)
    UNSPECIFIED = "unspecified"
    EXPORT_STATEMENT = "export_statement"
    IMPORT_STATEMENT = "import_statement"


Parent = TypeVar("Parent", bound="CodeBlock")


@apidoc
class Statement(Expression[Parent], Generic[Parent]):
    """Represents a single code statement, e.g. a function definition, an assignment, an if/else statement, etc."""

    statement_type: StatementType = StatementType.UNSPECIFIED
    _pos: int

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent, pos: int | None = None) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        self._pos = pos

    def __rich_repr__(self) -> rich.repr.Result:
        if self.parent:
            yield "level", self.parent.level
        yield from super().__rich_repr__()

    __rich_repr__.angular = ANGULAR_STYLE

    @property
    def index(self) -> int:
        """The 0-based index of the statement in the parent code block.

        Returns the sequential position of this statement within its containing code block.

        Returns:
            int: The 0-based index of this statement within its parent code block.
        """
        return self._pos

    @classmethod
    @noapidoc
    @final
    def from_code_block(cls, ts_node: TSNode, code_block: CodeBlock, pos: int | None = None) -> Statement:
        return cls(ts_node, code_block.file_node_id, code_block.ctx, parent=code_block, pos=pos)

    @cached_property
    @reader
    def nested_code_blocks(self) -> list[Parent]:
        """Returns all nested code blocks within the statement.

        Finds and parses any immediate 'block' or 'statement_block' nodes within the statement.

        Returns:
            list[TCodeBlock]: A list of parsed code blocks that are directly nested within this statement. Each block has a level one higher than its parent block.
        """
        block_nodes = find_all_descendants(self.ts_node, {"block", "statement_block"}, max_depth=1)

        nested_blocks = []
        for block_node in block_nodes:
            block = self.ctx.node_classes.code_block_cls(block_node, self.parent.level + 1, self.parent, self)
            block.parse()
            nested_blocks.append(block)
        return nested_blocks

    @property
    @reader
    def nested_statements(self) -> list[MultiLineCollection[Statement[Self], Parent]]:
        """Returns a list of statement collections within nested code blocks.

        Accesses and retrieves the statements from each code block nested within the current statement,
        such as the statements within if/else branches or loop bodies.

        Returns:
            A list where each element is a
                collection of statements from one nested code block. Returns an empty list if there are no
                nested code blocks.
        """
        nested_code_blocks = self.nested_code_blocks
        if len(nested_code_blocks) == 0:
            return []

        nested_statements = []
        for code_block in nested_code_blocks:
            nested_statements.append(code_block.statements)

        return nested_statements

    def _get_indent(self) -> int:
        from codegen.sdk.core.detached_symbols.code_block import CodeBlock

        if isinstance(self.parent, CodeBlock):
            return self.parent.level * 4
        return self.ts_node.start_point[1]

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None):
        self._add_all_identifier_usages(usage_type, dest=dest)
