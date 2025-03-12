from __future__ import annotations

from abc import abstractmethod
from collections import deque
from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from typing_extensions import deprecated

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind, UsageType
from codegen.sdk.core.expressions import Expression, Value
from codegen.sdk.core.statements.statement import Statement, StatementType
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.extensions.utils import find_line_start_and_end_nodes
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.core.assignment import Assignment
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.has_block import HasBlock
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.statements.assignment_statement import AssignmentStatement
    from codegen.sdk.core.statements.attribute import Attribute
    from codegen.sdk.core.statements.comment import Comment
    from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
    from codegen.sdk.core.statements.return_statement import ReturnStatement
    from codegen.sdk.core.statements.symbol_statement import SymbolStatement
    from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection
    from codegen.sdk.output.ast import AST


Parent = TypeVar("Parent", bound="HasBlock")
TAssignment = TypeVar("TAssignment", bound="Assignment")


@apidoc
class CodeBlock(Expression[Parent], Generic[Parent, TAssignment]):
    """Container class for a list of code Statements that share an indentation level, e.g. a
    function body or class body.

    Enables various types of queries and operations on the code block.

    Attributes:
        level: The indentation level of the code block.
        parent_block: The parent code block containing this block, or None if it is a top-level block.
    """

    level: int
    parent_block: CodeBlock | None
    _statements: MultiLineCollection[Statement, Self]

    def __init__(self, ts_node: TSNode, level: int, parent_block: CodeBlock | None, parent: Parent) -> None:
        super().__init__(ts_node, parent.file_node_id, parent.ctx, parent)
        self.parent_block = parent_block
        self.level = level
        # self.parse()

    @noapidoc
    def parse(self) -> None:
        self._statements = self._parse_statements()

    @abstractmethod
    @noapidoc
    def _parse_statements(self) -> MultiLineCollection[Statement, Self]:
        """Parses top level statements in the code block."""

    @property
    @reader
    def statements(self) -> MultiLineCollection[Statement, Self]:
        """Gets a view of the top-level statements in the code block.

        Returns a collection of statements that appear directly in this code block, ordered by their appearance.
        This does not include statements nested within other blocks (e.g., if statements, functions).

        Returns:
            MultiLineCollection[Statement, Self]: An ordered collection of top-level statements in the code block.
        """
        return self._statements

    @reader
    def _get_statements(self, statement_type: StatementType | None = None, max_level: int | None = None) -> Generator[Statement[Self]]:
        """Private implementation of get_statements that returns a generator of statements."""
        queue = deque([(self._statements, self.level)])
        while queue:
            current_statements, level = queue.popleft()

            for statement in current_statements:
                if statement_type is None or statement.statement_type == statement_type:
                    yield statement
                if statement.statement_type == StatementType.SYMBOL_STATEMENT:
                    continue
                if max_level is None or level < max_level:
                    for nested_statements in statement.nested_statements:
                        queue.append((nested_statements.symbols, level + 1))

    @reader
    def get_statements(self, statement_type: StatementType | None = None, max_level: int | None = None) -> list[Statement[Self]]:
        """Returns all statements of a given type up to the specified block level.

        This method retrieves statements from the code block and its nested blocks. Statements can be filtered by type and depth.

        Args:
            statement_type (StatementType | None): The type of statements to return. If None, returns all statement types.
            max_level (int | None): The maximum block depth level to search. If None, searches all levels.

        Returns:
            A sorted list of matching statements.
        """
        return sort_editables(self._get_statements(statement_type, max_level))

    @property
    @reader
    def symbol_statements(self) -> list[SymbolStatement]:
        """Returns list of top level symbol statements in the code block.

        Retrieves all statements in the block that have a statement type of SYMBOL_STATEMENT.
        Symbol statements are statements that declare or manipulate symbols like functions or classes.

        Returns:
            list[SymbolStatement]: A list of all the symbol statements at the top level of this code block.
        """
        return [x for x in self.statements if x.statement_type == StatementType.SYMBOL_STATEMENT]

    @property
    @reader
    def comments(self) -> list[Comment[Parent, Self]]:
        """Gets list of top level comments in the code block.

        Returns a list of comment statements that occur at the top level of this code block. Does not include nested comments.

        Returns:
            list[Comment[Parent, Self]]: A list of Comment objects that are immediate children of this code block.
        """
        return [x for x in self.statements if x.statement_type == StatementType.COMMENT]

    @reader
    def get_comment(self, comment_src: str) -> Comment[Parent, Self] | None:
        """Gets the first comment statement containing a specific text string.

        Searches through all nested statement levels in the code block to find a comment that contains
        the specified text.

        Args:
            comment_src (str): The text string to search for within comment statements.

        Returns:
            Comment[Parent, Self] | None: The first comment statement containing the search text,
                or None if no matching comment is found.
        """
        return next((x for x in self._get_statements(StatementType.COMMENT) if comment_src in x.source), None)

    @property
    @reader
    def if_blocks(self) -> list[IfBlockStatement[Self]]:
        """Returns a list of top level if statements in the code block.

        A property that retrieves all the immediate if statements within this code block.
        These are if statements that exist at the same indentation level as other statements in the block, not nested ones.

        Returns:
            list[IfBlockStatement[Parent, Self]]: A list of top-level if statement objects in the code block.
        """
        return [x for x in self.statements if x.statement_type == StatementType.IF_BLOCK_STATEMENT]

    @property
    @reader
    def attributes(self) -> list[Attribute[Parent, Self]]:
        """Returns a list of top level class attribute statements in the code block.

        Get all attribute statements (Attribute objects) that are direct children of the current code block.
        These represent class-level attribute declarations.

        Returns:
            list[Attribute[Parent, Self]]: A list of Attribute objects representing the class-level attributes,
                ordered by their appearance in the code block.
        """
        return [x for x in self.statements if x.statement_type == StatementType.CLASS_ATTRIBUTE]

    @reader
    def get_attributes(self, private: bool) -> list[Attribute[Parent, Self]]:
        """Returns attributes from the code block, with the option to include or exclude private
        attributes.

        Retrieves a list of top level attribute statements from the code block, filtering based on the private parameter.
        When private is True, both private and public attributes are returned. When private is False, only public
        attributes are returned.

        Args:
            private (bool): Whether to include private attributes in the returned list. If True, returns both private and
                public attributes. If False, returns only public attributes.

        Returns:
            list[Attribute[Parent, Self]]: A list of attribute statements matching the privacy criteria.
        """
        return [x for x in self.attributes if not x.is_private or private]

    @property
    @reader
    def assignment_statements(self) -> list[AssignmentStatement[Self, TAssignment]]:
        """Returns list of top level assignment statements in the code block.

        Retrieves all statements in the code block whose type is AssignmentStatement. These statements represent direct assignments
        at the current code block level (not nested within other blocks).

        Returns:
            A list of assignment statements found at the top level of the code block.
        """
        return [x for x in self.statements if x.statement_type == StatementType.ASSIGNMENT]

    @property
    @reader
    def return_statements(self) -> list[ReturnStatement[Self]]:
        """Gets all return statements at the top level of the code block.

        Args:
            None

        Returns:
            list[ReturnStatement[Parent, Self]]: A list of return statements that appear at the top level of the code block. Does not include return statements in nested blocks.
        """
        return [x for x in self.statements if x.statement_type == StatementType.RETURN_STATEMENT]

    @property
    @reader
    def assignments(self) -> list[Assignment[Parent, Self]]:
        """Returns all assignments in the code block across all nesting levels.

        Gets every assignment from every assignment statement in the code block, including assignments in nested blocks.

        Returns:
            list[Assignment[Parent, Self]]: A list of Assignment objects from all nested levels of the code block.
        """
        variables = []
        for statement in self._get_statements(StatementType.ASSIGNMENT):
            variables.extend([x for x in statement.assignments])
        return variables

    @reader
    def get_assignments(self, var_name: str, *, fuzzy: bool = False, parameters: bool = False) -> list[Assignment[Parent, Self]]:
        """Returns a list of assignments with the specified variable name.

        Returns all assignments in the code block that match the given variable name.

        Args:
            var_name (str): The name of the variable to find assignments for.

        Returns:
            list[Assignment[Parent, Self]]: A list of Assignment objects that match the variable name.
        """
        assignments = list(self.parent.parameters) + self.assignments if parameters else self.assignments

        return [x for x in assignments if (var_name in x.name if fuzzy else x.name == var_name)]

    @property
    @reader
    def local_var_assignments(self) -> list[Assignment[Parent, Self]]:
        """Returns all local variable assignment in the code block, for all nest levels.

        A property that returns all variable assignments that are marked as local variables within the code block,
        including assignments in nested code blocks.

        Returns:
            list[Assignment[Parent, Self]]: A list of Assignment objects representing local variable assignments.
        """
        return [x for x in self.assignments if x.is_local_variable]

    @reader
    def get_local_var_assignment(self, var_name: str) -> Assignment[Parent, Self] | None:
        """Returns the first code statement that assigns a local variable with the specified name.

        Searches through all local variable assignments in the code block and returns the first one that matches
        the given variable name.

        Args:
            var_name (str): The name of the local variable to search for.

        Returns:
            Assignment[Parent, Self] | None: The first matching local variable assignment, or None if no match is found.
        """
        return next((x for x in self.local_var_assignments if x.name == var_name), None)

    @reader
    def get_local_var_assignments(self, var_name: str, fuzzy_match: bool = False) -> list[Assignment[Parent, Self]]:
        """Returns all instances of local variable assignments that match the specified variable
        name.

        Finds local variable assignments within the code block that match the provided variable name, with optional fuzzy matching.

        Args:
            var_name (str): The name of the local variable to search for.
            fuzzy_match (bool, optional): If True, matches variables whose names contain var_name.
                If False, only matches exact variable names. Defaults to False.


        Returns:
            list[Assignment[Parent, Self]]: List of Assignment objects representing local variable assignments
                that match the specified name criteria.
        """
        return [x for x in self.local_var_assignments if (var_name in x.name if fuzzy_match else var_name == x.name)]

    @reader
    def get_variable_usages(self, var_name: str, fuzzy_match: bool = False) -> list[Editable[Self]]:
        """Returns all instances of variable usages in a code block.

        This method searches through all statements in the code block to find variable usages that match the specified variable name.
        Variable usages are instances where the variable is referenced or used in expressions, function calls, or other code constructs.

        Args:
            var_name (str): The name of the variable to search for.
            fuzzy_match (bool): When True, matches on variable names that contain var_name. When False (default), only matches exact variable names.

        Returns:
            list[Editable[Self]]: A sorted list of variable usage instances as Editable objects.
        """
        usages = list()
        for assignment in self.get_assignments(var_name, fuzzy=fuzzy_match, parameters=True):
            usages.extend(usage.match for usage in assignment.usages(UsageType.DIRECT | UsageType.CHAINED))
        return sort_editables(usages)

    @writer
    def rename_variable_usages(self, old_var_name: str, new_var_name: str, fuzzy_match: bool = False) -> None:
        """Renames all instances of variable usages in the code block.

        This method modifies variable usages in the code block by replacing occurrences of the old variable name with a new one.
        It uses get_assignments() and rename() internally to find all instances of the variable.

        Args:
            old_var_name (str): The current name of the variable to rename.
            new_var_name (str): The new name to give the variable.
            fuzzy_match (bool): When True, matches variables containing old_var_name. When False, only exact matches. Defaults to False.

        Returns:
            None: This method mutates the code block in place.
        """
        for assignment in self.get_assignments(old_var_name, fuzzy=fuzzy_match, parameters=True):
            assignment.rename(assignment.name.replace(old_var_name, new_var_name))

    @deprecated("Use `self.statements.insert(0, ...)` instead.")
    @writer
    def insert_before(self, new_src: str) -> None:
        """Inserts new source code at the top of the code block.

        This method has been deprecated in favor of using `self.statements.insert(0, ...)`.

        Args:
            new_src (str): The source code to insert at the top of the code block.

        Returns:
            None
        """
        start_lines = self._get_line_starts()
        start_line = start_lines[0]
        start_line.insert_before(new_src, fix_indentation=True, newline=True)

    @deprecated("Use `self.statements.append(...)` instead.")
    @writer
    def insert_after(self, new_src: str, fix_indentation=True, newline=True) -> None:
        """Inserts source code at the bottom of the code block.

        This method is deprecated. Use `self.statements.append(...)` instead.

        Args:
            new_src (str): The source code to insert.
            fix_indentation (bool): Whether to fix the indentation of the inserted code. Defaults to True.
            newline (bool): Whether to add a newline before the inserted code. Defaults to True.

        Returns:
            None
        """
        if fix_indentation is False:
            super().insert_after(new_src, fix_indentation=fix_indentation, newline=newline)
        end_lines = self._get_line_ends()
        end_line = end_lines[-1]
        end_line.insert_after(new_src, fix_indentation=fix_indentation, newline=newline)

    @writer
    def indent(self, level: int) -> None:
        """Adjusts the indentation level of the entire code block.

        Modifies the indentation of all lines in the code block by adding or removing spaces at the start of each line.
        The amount of indentation per level is determined by either the existing indentation level or defaults to 4 spaces.

        Args:
            level (int): The number of indentation levels to adjust. Positive values indent right, negative values indent left.

        Returns:
            None
        """
        if level == 0:
            return

        start_lines = self._get_line_starts()
        indent_size = int(start_lines[0].start_point[1] / self.level) if self.level > 0 else 4
        total_indent_size = indent_size * abs(level)
        for start_node in start_lines:
            if level < 0:
                (_, column) = start_node.start_point
                new_column = max(0, column - total_indent_size)
                offset = column - new_column
                start_node.remove_byte_range(start_node.start_byte - offset, start_node.start_byte)
            else:
                start_node.insert_before(" " * total_indent_size, newline=False)

    @writer
    def wrap(self, before_src: str, after_src: str = "") -> None:
        """Wraps a code block with a statement and indents it.

        This method wraps an existing code block with a preceding statement (and optionally a following statement),
        and indents the block appropriately. Common use cases include wrapping code blocks with if statements,
        try/except blocks, with statements, or other control flow structures.

        Args:
            before_src (str): The source code to insert before the block.
            after_src (str): The source code to insert after the block. Defaults to an empty string.

        Returns:
            None
        """
        # Step 1: Add before_src before the block
        self.insert_before(before_src)

        # Step 2: Add after_src before the block
        if after_src:
            self.insert_after(after_src)

        # Step 3: Indent the block
        self.indent(1)

    @writer
    def unwrap(self) -> None:
        """Extracts a code block from its parent wrapper container by removing the wrapping
        statement and adjusting indentation.

        This method unwraps a code block from its parent container (like if statements, with statements, function definitions, etc.)
        by removing the parent wrapper code and unindenting the block content.

        This method handles two cases:
        1. When the wrapper is the only statement on its line
        2. When the wrapper shares a line with other statements

        For example, transforming:
            if a:
                return b
        into:
            return b

        Args:
            None

        Returns:
            None
        """
        self.indent(-1)

        # If the wrapper doesn't start at the beginning of the line, only remove up to the end of the wrapper
        wrapper_row = self.ts_node.parent.start_point[0]
        if (prev_sibling := self.ts_node.parent.prev_sibling) is not None and prev_sibling.start_point[0] == wrapper_row:
            while prev_sibling.prev_sibling and prev_sibling.prev_sibling.start_point[0] == wrapper_row:
                prev_sibling = prev_sibling.prev_sibling

            remove_start_byte = prev_sibling.start_byte - 1
            wrapper_line_nodes = find_line_start_and_end_nodes(self.ts_node.parent)
            wrapper_end_row = self.statements[0].start_point[0] - 1
            wrapper_end_node = next(x[1] for x in wrapper_line_nodes if x[1].start_point[0] == wrapper_end_row)
            self.remove_byte_range(remove_start_byte, wrapper_end_node.end_byte)

        # Else, remove the entire top wrapper up to the start of the block
        else:
            self.remove_byte_range(self.ts_node.parent.start_byte, self.statements[0].start_byte)

    @reader
    @noapidoc
    def _get_line_starts(self) -> list[Editable]:
        """Returns an ordered list of nodes located at the left-most of each line in the code block
        eg.

        Given the code:
        ```
        def foo():
            x = 1
            y = 2
        ```
        returns [Node(def foo():), Node(x), Node(y)]
        """
        starts = []
        for comment in self.get_statements(statement_type=StatementType.COMMENT, max_level=self.level):
            if comment.start_byte < self.start_byte:
                starts.append(comment)
        starts.extend([Value(x[0], self.file_node_id, self.ctx, self) for x in find_line_start_and_end_nodes(self.ts_node)])
        return starts

    @reader
    @noapidoc
    def _get_line_ends(self) -> list[Editable]:
        """Returns an ordered list of nodes located at the right-most of each line in the code block
        eg.

        Given the code:
        ```
        def foo():
            x = 1
            y = 2
        ```
        returns [Node(def foo():), Node(1), Node(2)]
        """
        ends = []
        for comment in self.get_statements(statement_type=StatementType.COMMENT, max_level=self.level):
            if comment.start_byte < self.start_byte:
                ends.append(comment)
        ends.extend([Value(x[1], self.file_node_id, self.ctx, self) for x in find_line_start_and_end_nodes(self.ts_node)])
        return ends

    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        dest = dest or self.parent.self_dest
        for statement in self.statements:
            statement._compute_dependencies(UsageKind.BODY, dest)

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns a list of all function calls in the code block.

        Gets a list of all function calls in the code block, including those within nested statements. The function calls are ordered by their appearance in the code block.

        Returns:
            list[FunctionCall]: A list of FunctionCall objects representing all function calls in the code block.
        """
        fcalls = []
        for s in self.statements:
            fcalls.extend(s.function_calls)
        return fcalls

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = []
        for s in self.get_statements():
            symbols.extend(s.descendant_symbols)
        return symbols

    def _smart_remove(self, child, *args, **kwargs) -> bool:
        if len(self.statements) <= 1 and self.level > 0:
            self.parent.remove(*args, **kwargs)
            return True
        return False

    @override
    def _get_ast_children(self) -> list[tuple[str | None, AST]]:
        return [("statements", self._statements.ast())]
