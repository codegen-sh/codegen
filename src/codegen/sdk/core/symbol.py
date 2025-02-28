from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, Literal, TypeVar

from rich.markup import escape

from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind, UsageType
from codegen.sdk.core.detached_symbols.argument import Argument
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.expressions import Name, Value
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.core.expressions.defined_name import DefinedName
from codegen.sdk.core.interfaces.usable import Usable
from codegen.sdk.core.statements.statement import Statement
from codegen.sdk.enums import ImportType, NodeType, SymbolType
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.output.constants import ANGULAR_STYLE
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    import rich.repr
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.export import Export
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.has_block import HasBlock
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.symbol_groups.comment_group import CommentGroup

Parent = TypeVar("Parent", bound="HasBlock")
TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock")


@apidoc
class Symbol(Usable[Statement["CodeBlock[Parent, ...]"]], Generic[Parent, TCodeBlock]):
    """Abstract representation of a Symbol in a Codebase. A Symbol is a top-level entity in a file, e.g. a Function, Class, GlobalVariable, etc.

    Attributes:
        symbol_type: The type of the symbol.
        node_type: The type of the node, set to NodeType.SYMBOL.
    """

    symbol_type: SymbolType
    node_type: Literal[NodeType.SYMBOL] = NodeType.SYMBOL

    def __init__(
        self,
        ts_node: TSNode,
        file_id: NodeId,
        ctx: CodebaseContext,
        parent: Statement[CodeBlock[Parent, ...]],
        name_node: TSNode | None = None,
        name_node_type: type[Name] = DefinedName,
    ) -> None:
        super().__init__(ts_node, file_id, ctx, parent)
        name_node = self._get_name_node(ts_node) if name_node is None else name_node
        self._name_node = self._parse_expression(name_node, default=name_node_type)
        from codegen.sdk.core.interfaces.has_block import HasBlock

        if isinstance(self, HasBlock):
            self.code_block = self._parse_code_block()
        self.parse(ctx)
        if isinstance(self, HasBlock):
            self.code_block.parse()

    def __rich_repr__(self) -> rich.repr.Result:
        yield escape(self.filepath) + "::" + (self.full_name if self.full_name else "<no name>")

    __rich_repr__.angular = ANGULAR_STYLE

    @property
    @noapidoc
    def parent_symbol(self) -> Symbol | SourceFile | Import | Export:
        """Returns the parent symbol of the symbol."""
        from codegen.sdk.core.export import Export

        parent = super().parent_symbol
        if parent == self.file or isinstance(parent, Export):
            # Top level symbol
            return self
        return parent

    @staticmethod
    @noapidoc
    def _get_name_node(ts_node: TSNode) -> TSNode | None:
        """Returns the ID node from the root node of the symbol."""
        return ts_node.child_by_field_name("name")

    @property
    @reader(cache=False)
    def extended_nodes(self) -> list[Editable]:
        """Returns a list of Editable nodes associated with this symbol, including extended symbols.

        Extended symbols include `export`, `public`, `decorator`, comments, and inline comments.

        Args:
            self: The symbol instance.

        Returns:
            list[Editable]: A list of Editable nodes containing the current symbol and its extended symbols,
                sorted in the correct order.
        """
        from codegen.sdk.core.interfaces.has_block import HasBlock

        comment_nodes = self.comment.symbols if self.comment else []
        inline_comment_nodes = self.inline_comment.symbols if self.inline_comment else []
        nodes = [self, *comment_nodes, *inline_comment_nodes]
        new_ts_node = self.ts_node

        if isinstance(self, HasBlock) and self.is_decorated:
            new_ts_node = self.ts_node.parent

        extended_nodes = [(Value(new_ts_node, self.file_node_id, self.ctx, self.parent) if node.ts_node == self.ts_node else node) for node in nodes]
        return sort_editables(extended_nodes)

    @writer
    def edit(self, new_src: str, fix_indentation: bool = False, priority: int = 0, dedupe: bool = True) -> None:
        """Replace the source of this node with new_src.

        Edits the source code of this node by replacing it with the provided new source code. If specified, the indentation of
        the new source can be adjusted to match the current text's indentation.

        Args:
            new_src (str): The new source code to replace the current source with.
            fix_indentation (bool): If True, adjusts the indentation of new_src to match the current text's indentation. Defaults to False.
            priority (int): The priority of this edit. Higher priority edits take precedence. Defaults to 0.
            dedupe (bool): If True, prevents duplicate edits. Defaults to True.

        Returns:
            None
        """
        self.extended.edit(new_src, fix_indentation=fix_indentation, priority=priority, dedupe=dedupe)

    @property
    @reader
    def source(self) -> str:
        """Returns the source code of the symbol.

        Gets the source code of the symbol from its extended representation, which includes any comments, docstrings, access identifiers, or decorators.

        Returns:
            str: The complete source code of the symbol including any extended nodes.
        """
        return self.extended.source

    @source.setter
    @writer
    def source(self, value) -> None:
        """Sets the source code text of this Symbol.

        Replaces the current source code text with a new value by calling the edit method.

        Args:
            value (str): The new source code text to replace the current text with.

        Returns:
            None
        """
        if self.source != value:
            self.edit(value)

    @property
    @abstractmethod
    @reader
    def comment(self) -> CommentGroup | None:
        """Returns the comment group associated with the symbol, if any.

        Returns:
            CommentGroup | None: The comment group containing all comments associated with the symbol if it exists, None otherwise.
        """

    @property
    @abstractmethod
    @reader
    def inline_comment(self) -> CommentGroup | None:
        """Returns the inline comment group associated with the symbol, if any.

        Returns:
            CommentGroup | None: The inline comment group object associated with the symbol, or None if no inline comment exists.
        """

    @abstractmethod
    @writer
    def set_comment(self, comment: str) -> None:
        """Sets a comment to the symbol.

        Updates or creates a comment for the symbol. If a comment already exists, it will be overridden.
        If no comment exists, a new comment group will be created.

        Args:
            comment (str): The comment text to set.

        Returns:
            None
        """

    @abstractmethod
    @writer
    def add_comment(self, comment: str) -> None:
        """Adds a comment to the symbol.

        Adds a comment to the top of a symbol. If a comment group already exists, the new comment will be appended
        to the existing comment group. If no comment group exists, a new comment group will be created.

        Args:
            comment (str): The comment text to add.

        Returns:
            None
        """

    @abstractmethod
    @writer
    def set_inline_comment(self, comment: str) -> None:
        """Sets an inline comment to the symbol.

        Adds or updates an inline comment for the symbol with the provided text. If an inline comment already exists,
        it will be overridden. If no inline comment exists, a new inline comment will be created.

        Args:
            comment (str): The text of the inline comment to be added or updated.

        Returns:
            None
        """

    @noapidoc
    @commiter
    def parse(self, ctx: CodebaseContext) -> None:
        """Adds itself as a symbol node in the graph, and an edge from the parent file to itself."""

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################
    @writer
    def insert_before(self, new_src: str, fix_indentation: bool = False, newline: bool = True, priority: int = 0, dedupe: bool = True, extended: bool = True) -> None:
        """Inserts text before the current symbol node in the Abstract Syntax Tree.

        Handles insertion of new source code before a symbol, with special handling for extended nodes like comments and decorators.
        The insertion can be done either before the symbol itself or before its extended nodes.

        Args:
            new_src (str): The source code text to insert.
            fix_indentation (bool): Whether to adjust the indentation of new_src to match current text. Defaults to False.
            newline (bool): Whether to add a newline after insertion. Defaults to True.
            priority (int): Priority of this edit operation. Higher priority edits are applied first. Defaults to 0.
            dedupe (bool): Whether to remove duplicate insertions. Defaults to True.
            extended (bool): Whether to insert before extended nodes like comments and decorators. Defaults to True.

        Returns:
            None
        """
        if extended:
            first_node = self.extended_nodes[0]
            # Skip extension for the child node
            if isinstance(first_node, Symbol):
                return first_node.insert_before(new_src, fix_indentation, newline, priority, dedupe, extended=False)
            else:
                return first_node.insert_before(new_src, fix_indentation, newline, priority, dedupe)
        return super().insert_before(new_src, fix_indentation, newline, priority, dedupe)

    def move_to_file(
        self,
        file: SourceFile,
        include_dependencies: bool = True,
        strategy: Literal["add_back_edge", "update_all_imports", "duplicate_dependencies"] = "update_all_imports",
    ) -> None:
        """Moves the given symbol to a new file and updates its imports and references.

        This method moves a symbol to a new file and updates all references to that symbol throughout the codebase. The way imports are handled can be controlled via the strategy parameter.

        Args:
            file (SourceFile): The destination file to move the symbol to.
            include_dependencies (bool): If True, moves all dependencies of the symbol to the new file. If False, adds imports for the dependencies. Defaults to True.
            strategy (str): The strategy to use for updating imports. Can be either 'add_back_edge' or 'update_all_imports'. Defaults to 'update_all_imports'.
                - 'add_back_edge': Moves the symbol and adds an import in the original file
                - 'update_all_imports': Updates all imports and usages of the symbol to reference the new file

        Returns:
            None

        Raises:
            AssertionError: If an invalid strategy is provided.
        """
        encountered_symbols = {self}
        self._move_to_file(file, encountered_symbols, include_dependencies, strategy)

    @noapidoc
    def _move_to_file(
        self,
        file: SourceFile,
        encountered_symbols: set[Symbol | Import],
        include_dependencies: bool = True,
        strategy: Literal["add_back_edge", "update_all_imports", "duplicate_dependencies"] = "update_all_imports",
    ) -> tuple[NodeId, NodeId]:
        """Helper recursive function for `move_to_file`"""
        from codegen.sdk.core.import_resolution import Import

        # =====[ Arg checking ]=====
        if file == self.file:
            return file.file_node_id, self.node_id
        if imp := file.get_import(self.name):
            encountered_symbols.add(imp)
            imp.remove()

        if include_dependencies:
            # =====[ Move over dependencies recursively ]=====
            for dep in self.dependencies:
                if dep in encountered_symbols:
                    continue

                # =====[ Symbols - move over ]=====
                if isinstance(dep, Symbol) and dep.is_top_level:
                    encountered_symbols.add(dep)
                    dep._move_to_file(
                        file=file,
                        encountered_symbols=encountered_symbols,
                        include_dependencies=include_dependencies,
                        strategy=strategy,
                    )

                # =====[ Imports - copy over ]=====
                elif isinstance(dep, Import):
                    if dep.imported_symbol:
                        file.add_import(imp=dep.imported_symbol, alias=dep.alias.source)
                    else:
                        file.add_import(imp=dep.source)
        else:
            for dep in self.dependencies:
                # =====[ Symbols - add back edge ]=====
                if isinstance(dep, Symbol) and dep.is_top_level:
                    file.add_import(imp=dep, alias=dep.name, import_type=ImportType.NAMED_EXPORT, is_type_import=False)
                elif isinstance(dep, Import):
                    if dep.imported_symbol:
                        file.add_import(imp=dep.imported_symbol, alias=dep.alias.source)
                    else:
                        file.add_import(imp=dep.source)

        # =====[ Make a new symbol in the new file ]=====
        file.add_symbol(self)
        import_line = self.get_import_string(module=file.import_module_name)

        # =====[ Checks if symbol is used in original file ]=====
        # Takes into account that it's dependencies will be moved
        is_used_in_file = any(
            usage.file == self.file and usage.node_type == NodeType.SYMBOL and usage not in encountered_symbols and (usage.start_byte < self.start_byte or usage.end_byte > self.end_byte)  # HACK
            for usage in self.symbol_usages
        )

        # ======[ Strategy: Duplicate Dependencies ]=====
        if strategy == "duplicate_dependencies":
            # If not used in the original file. or if not imported from elsewhere, we can just remove the original symbol
            if not is_used_in_file and not any(usage.kind is UsageKind.IMPORTED and usage.usage_symbol not in encountered_symbols for usage in self.usages):
                self.remove()

        # ======[ Strategy: Add Back Edge ]=====
        # Here, we will add a "back edge" to the old file importing the symbol
        elif strategy == "add_back_edge":
            if is_used_in_file or any(usage.kind is UsageKind.IMPORTED and usage.usage_symbol not in encountered_symbols for usage in self.usages):
                self.file.add_import(imp=import_line)
            # Delete the original symbol
            self.remove()

        # ======[ Strategy: Update All Imports ]=====
        # Update the imports in all the files which use this symbol to get it from the new file now
        elif strategy == "update_all_imports":
            for usage in self.usages:
                if isinstance(usage.usage_symbol, Import) and usage.usage_symbol.file != file:
                    # Add updated import
                    usage.usage_symbol.file.add_import(import_line)
                    usage.usage_symbol.remove()
                elif usage.usage_type == UsageType.CHAINED:
                    # Update all previous usages of import * to the new import name
                    if usage.match and "." + self.name in usage.match:
                        if isinstance(usage.match, FunctionCall) and self.name in usage.match.get_name():
                            usage.match.get_name().edit(self.name)
                        if isinstance(usage.match, ChainedAttribute):
                            usage.match.edit(self.name)
                        usage.usage_symbol.file.add_import(imp=import_line)

            # Add the import to the original file
            if is_used_in_file:
                self.file.add_import(imp=import_line)
            # Delete the original symbol
            self.remove()

    @property
    @reader
    @noapidoc
    def is_top_level(self) -> bool:
        """Is this symbol a top-level symbol: does it have a level of 0?"""
        from codegen.sdk.core.file import File

        parent = self.parent
        while not isinstance(parent, Symbol | Argument):
            if isinstance(parent, File):
                return True
            parent = parent.parent
        return False

    @writer
    def add_keyword(self, keyword: str) -> None:
        """Insert a keyword in the appropriate place before this symbol if it doesn't already exist.

        This method adds a keyword (e.g., 'public', 'async', 'static') in the syntactically appropriate
        position relative to other keywords. If the keyword already exists, no action is taken.

        Args:
            keyword (str): The keyword to be inserted. Must be a valid keyword in the language context.

        Raises:
            AssertionError: If the provided keyword is not in the language's valid keywords list.
        """
        assert keyword in self.ctx.node_classes.keywords
        to_insert_onto = None
        to_insert_idx = self.ctx.node_classes.keywords.index(keyword)
        for node in self.children_by_field_types(self.ctx.node_classes.keywords):
            idx = self.ctx.node_classes.keywords.index(node)
            if node == keyword:
                return
            if idx < to_insert_idx:
                to_insert_onto = node
        if to_insert_onto is not None:
            to_insert_onto.insert_after(" " + keyword, newline=False)
        else:
            self.insert_before(keyword + " ", newline=False, extended=False)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        from codegen.sdk.core.interfaces.has_block import HasBlock

        symbols = [self]
        if isinstance(self, HasBlock):
            symbols.extend(self.code_block.descendant_symbols)
        return symbols
