from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar, Generic, Literal, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.codebase.transactions import TransactionPriority
from codegen.sdk.core.autocommit import commiter, reader, remover, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.core.interfaces.usable import Usable
from codegen.sdk.core.statements.import_statement import ImportStatement
from codegen.sdk.enums import EdgeType, ImportType, NodeType
from codegen.sdk.extensions.utils import cached_property
from codegen.sdk.output.constants import ANGULAR_STYLE
from codegen.shared.decorators.docs import apidoc, noapidoc
from codegen.visualizations.enums import VizNode

if TYPE_CHECKING:
    from collections.abc import Generator

    import rich.repr
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.interfaces.exportable import Exportable
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.symbol import Symbol


TSourceFile = TypeVar("TSourceFile", bound="SourceFile")


@dataclass
class ImportResolution(Generic[TSourceFile]):
    """Represents the resolution of an import statement to a symbol defined in another file.

    Has the following properties:
    - from_file: Optional[SourceFile]. None when import resolves to an external module
    - symbol: Optional[Union[Symbol, ExternalModule]]. None when import resolves to an external module
    - imports_file: bool. True when we import the entire file (e.g. `from a.b.c import foo`)
    """

    from_file: TSourceFile | None = None  # SourceFile object. None when import resolves to an external module
    symbol: Symbol | ExternalModule | None = None  # None when we import the entire file (e.g. `from a.b.c import foo`)
    imports_file: bool = False  # True when we import the entire file (e.g. `from a.b.c import foo`)


TSourceFile = TypeVar("TSourceFile", bound="SourceFile")


@apidoc
class Import(Usable[ImportStatement], Chainable, Generic[TSourceFile], HasAttribute[TSourceFile]):
    """Represents a single symbol being imported.

    Attributes:
        to_file_id: The node ID of the file to which this import belongs.
        module: The module from which the symbol is being imported, if applicable.
        symbol_name: The name of the symbol being imported. For instance import a as b has a symbol_name of a.
        alias: The alias of the imported symbol, if one exists.
        node_type: The type of node, set to NodeType.IMPORT.
        import_type: The type of import, indicating how the symbol is imported.
        import_statement: The statement that this import is part of.
        import_statement: the ImportStatement that this import belongs to
    """

    to_file_id: NodeId
    module: Editable | None
    symbol_name: Editable | None
    alias: Editable | None
    node_type: ClassVar[Literal[NodeType.IMPORT]] = NodeType.IMPORT
    import_type: ImportType
    import_statement: ImportStatement

    def __init__(
        self,
        ts_node: TSNode,
        file_node_id: NodeId,
        ctx: CodebaseContext,
        parent: ImportStatement,
        module_node: TSNode | None,
        name_node: TSNode | None,
        alias_node: TSNode | None,
        import_type: ImportType = ImportType.UNKNOWN,
    ) -> None:
        self.to_file_id = file_node_id
        super().__init__(ts_node, file_node_id, ctx, parent)
        self.module = self.ctx.parser.parse_expression(module_node, self.file_node_id, ctx, self, default=Name) if module_node else None
        self.alias = self.ctx.parser.parse_expression(alias_node, self.file_node_id, ctx, self, default=Name) if alias_node else None
        self.symbol_name = self.ctx.parser.parse_expression(name_node, self.file_node_id, ctx, self, default=Name) if name_node else None
        self._name_node = self._parse_expression(name_node, default=Name)
        self.import_type = import_type

    def __rich_repr__(self) -> rich.repr.Result:
        if self.module:
            yield "module", self.module.source
        if self.name:
            yield "name", self.name
        if self.alias:
            yield "alias", self.alias.source, self.name
        yield "wildcard", self.is_wildcard_import(), False
        yield from super().__rich_repr__()

    __rich_repr__.angular = ANGULAR_STYLE

    @noapidoc
    @abstractmethod
    def resolve_import(self, base_path: str | None = None, *, add_module_name: str | None = None) -> ImportResolution[TSourceFile] | None:
        """Resolves the import to a symbol defined outside the file.

        Returns an ImportResolution object.
        """

    @noapidoc
    @commiter
    def add_symbol_resolution_edge(self) -> None:
        """Resolves the import to a symbol defined outside the file.

        If import is successfully resolved, a new edge is added to the graph. Must be called after
        `parse()` has been called for every file in the codebase. Returns the node id of the
        resolved import object.
        """
        resolution = self.resolve_import()

        # =====[ Case: Can't resolve the filepath ]=====
        if resolution is None:
            # =====[ Check if we are importing an external module in the graph ]=====
            ext = self.ctx.get_external_module(self.source, self._unique_node.source)
            if ext is None:
                ext = ExternalModule.from_import(self)
            self.ctx.add_edge(self.node_id, ext.node_id, type=EdgeType.IMPORT_SYMBOL_RESOLUTION)
        # =====[ Case: Can resolve the filepath ]=====
        elif resolution.symbol:
            if resolution.symbol.node_id == self.node_id:
                return []  # Circular to self
            self.ctx.add_edge(
                self.node_id,
                resolution.symbol.node_id,
                type=EdgeType.IMPORT_SYMBOL_RESOLUTION,
            )

        elif resolution.imports_file:
            self.ctx.add_edge(self.node_id, resolution.from_file.node_id, type=EdgeType.IMPORT_SYMBOL_RESOLUTION)
            # for symbol in resolution.from_file.symbols:
            #     usage = SymbolUsage(parent_symbol_name=self.name, child_symbol_name=self.name, type=SymbolUsageType.IMPORTED, match=self, usage_type=UsageType.DIRECT)
            #     self.ctx.add_edge(self.node_id, symbol.node_id, type=EdgeType.SYMBOL_USAGE, usage=usage)

        #  Referenced symbols that we can't find.
        #  Could be:
        #   - a broken import
        #   - it's actually importing a full file (i.e. resolution.imports_file should be True)
        #   - an indirect import of an external module
        # TODO: add as external module only if it resolves to an external module from resolution.from_file
        # Solution: return the resolution object to be processed in a separate loop in `compute_codebase_graph`
        return []

    @property
    @reader
    def name(self) -> str | None:
        """Returns the name or alias of the symbol being imported.

        Returns an identifier for the import which can be either the alias name of an imported symbol if it exists, or None.
        For example, in `from a.b import c as d`, this returns 'd'.
        For example, in `import { c as d } from 'a/b'`, this returns 'd'.

        Args:
            None

        Returns:
            str | None: The alias of the imported symbol if it exists, otherwise None.
        """
        if self.alias is None:
            return None
        return self.alias.source

    @reader
    def is_aliased_import(self) -> bool:
        """Returns True if this import is aliased.

        Checks if the current import has an alias that is different from its original name.
        For example, in 'from foo import bar as baz', returns True because 'baz' is different from 'bar'.
        In 'from foo import bar', returns False because there is no alias.

        Args:
            None

        Returns:
            bool: True if the import has an alias different from its original name, False otherwise.
        """
        if self.alias is None or self.symbol_name is None:
            return False
        return self.alias.source != self.symbol_name.source

    @abstractmethod
    def is_module_import(self) -> bool:
        """Returns True if this import is importing an entire module/file.

        Used to identify module imports vs symbol imports. This method evaluates whether
        the import is bringing in an entire module rather than specific symbols.

        Returns:
            bool: True if this import represents a module/file import, False if it represents a symbol import.
        """

    @reader
    def is_symbol_import(self) -> bool:
        """Returns True if this import is importing a symbol rather than a module.

        A symbol import is any import that references a specific object from a module, rather than importing the entire module. This method is the opposite of `is_module_import`.

        Returns:
            bool: True if this import is a symbol import, False if it is a module import.
        """
        return not self.is_module_import()

    @reader
    def is_wildcard_import(self) -> bool:
        """Returns True if the import symbol is a wildcard import.

        Determines whether this Import is a wildcard import, which means it imports all named exports from a module.
        Wildcard imports are represented using `*` in Python (e.g. `from module import *`)
        or `*` in TypeScript (e.g. `import * as name from 'module'`).

        Returns:
            bool: True if this is a wildcard import, False otherwise.
        """
        return self.import_type == ImportType.WILDCARD

    @property
    @abstractmethod
    def namespace(self) -> str | None:
        """Returns the namespace prefix that must be used with dot notation to reference the
        imported symbol.

        The namespace is the prefix required to access the imported symbol through dot notation.
        For example, in 'import foo as bar', bar is the namespace needed to access foo's exports as 'bar.xyz'.

        Returns:
            str | None: The namespace prefix if one exists, None otherwise.
                - For symbol imports or unnamed wildcard imports: None
                - For module imports: The module name or the module alias
        """

    @property
    @reader
    def from_file(self) -> TSourceFile | None:
        """Returns the SourceFile that an Import is importing from.

        This property traverses the Symbol edge to find the source file where the imported symbol is defined.

        Args:
            None

        Returns:
            TSourceFile | None: The SourceFile containing the imported symbol.
                Returns None if:
                - The import resolves to an external module
                - The imported symbol cannot be resolved
        """
        imported = self.imported_symbol
        if imported is None:
            return None
        elif imported.node_type == NodeType.EXTERNAL:
            return None
        elif imported.__class__.__name__.endswith("SourceFile"):  # TODO - this is a hack for when you import a full file/module
            return imported
        else:
            return imported.file

    @property
    @reader
    def to_file(self) -> TSourceFile:
        """SourceFile that this import resides in.

        Returns the source file in which the current import statement is located. This property helps track the location
        and context of import statements within the codebase graph.

        Returns:
            TSourceFile: The source file containing this import statement.
        """
        return self.ctx.get_node(self.to_file_id)

    @property
    @reader
    def resolved_symbol(self) -> Symbol | ExternalModule | TSourceFile | None:
        """Returns the symbol, source file, or external module that this import ultimately resolves
        to.

        This method follows indirect import chains to find the final resolved object. For example, if file A imports from B, which imports from C, this method returns the object from C.

        Returns:
            Symbol | ExternalModule | TSourceFile | None: The final resolved object that this import points to.
                - Symbol: If the import resolves to a symbol defined in the codebase
                - ExternalModule: If the import resolves to an external module
                - TSourceFile: If the import resolves to an entire source file
                - None: If the import cannot be resolved

        Note:
            If there is a circular import chain, returns the first repeated import in the chain.
        """
        # TODO: rename to `resolved_object` to capture that it can return a SourceFile instance as well
        imports_seen = set()
        resolved_symbol = self.imported_symbol

        while resolved_symbol is not None and resolved_symbol.node_type == NodeType.IMPORT:
            if resolved_symbol in imports_seen:
                return resolved_symbol

            imports_seen.add(resolved_symbol)
            resolved_symbol = resolved_symbol.imported_symbol

        return resolved_symbol

    @reader
    def _imported_symbol(self, resolve_exports: bool = False) -> Symbol | ExternalModule | TSourceFile | Import | None:
        """Returns the symbol directly being imported, including an indirect import and an External
        Module.
        """
        from codegen.sdk.python.file import PyFile
        from codegen.sdk.typescript.file import TSFile

        symbol = next(iter(self.ctx.successors(self.node_id, edge_type=EdgeType.IMPORT_SYMBOL_RESOLUTION, sort=False)), None)
        if symbol is None:
            # Unresolve import - could occur during unparse()
            return None
        if resolve_exports and isinstance(symbol, TSFile):
            name = self.symbol_name.source if self.symbol_name else ""
            if self.import_type == ImportType.DEFAULT_EXPORT:
                assert isinstance(symbol, TSFile)
                default = symbol
                if len(symbol.default_exports) == 1 and name != symbol.name:
                    default = symbol.default_exports[0]
                return symbol.valid_import_names.get(name, default)
            if self.import_type == ImportType.NAMED_EXPORT:
                if export := symbol.valid_import_names.get(name, None):
                    return export
        elif resolve_exports and isinstance(symbol, PyFile):
            name = self.symbol_name.source if self.symbol_name else ""
            if self.import_type == ImportType.NAMED_EXPORT:
                if symbol.name == name:
                    return symbol
                if imp := symbol.valid_import_names.get(name, None):
                    return imp

        if symbol is not self:
            return symbol

    @property
    @reader
    def imported_symbol(self) -> Symbol | ExternalModule | TSourceFile | Import | None:
        """Returns the symbol directly being imported, including an indirect import and an External
        Module.

        This property resolves the import's target and handles export-chain resolution. If the imported symbol
        is an export, this method will follow the export chain until it reaches the final target.

        Returns:
            Union[Symbol, ExternalModule, TSourceFile, Import, None]: The final resolved import target.
            Can be:
                - Symbol: The imported symbol
                - ExternalModule: If import resolves to an external module
                - SourceFile: If importing an entire file/module
                - Import: If there is a circular import
                - None: If the import is unresolved
        """
        if symbol := self._imported_symbol():
            while symbol and symbol.node_type == NodeType.EXPORT:
                symbol = symbol.exported_symbol
            return symbol

    @property
    @abstractmethod
    def imported_exports(self) -> list[Exportable]:
        """Returns the enumerated list of symbols imported from a module import.

        If the import represents a module/file import, returns a list of all exported symbols from that module.
        If the import is a symbol import, returns a list containing only the imported symbol.

        Returns:
            list[Exportable]: A list of exported symbols. For module imports, contains all exports from the module.
                For symbol imports, contains only the single imported symbol.
        """

    @property
    @reader
    def is_dynamic(self) -> bool:
        """Determines if this import is dynamically loaded based on its parent symbol.

        A dynamic import is one that appears within control flow or scope-defining statements, such as:
        - Inside function definitions
        - Inside class definitions
        - Inside if/else blocks
        - Inside try/except blocks
        - Inside with statements

        Dynamic imports are only loaded when their containing block is executed, unlike
        top-level imports which are loaded when the module is imported.

        Examples:
            Dynamic imports:
            ```python
            def my_function():
                import foo  # Dynamic - only imported when function runs


            if condition:
                from bar import baz  # Dynamic - only imported if condition is True

            with context():
                import qux  # Dynamic - only imported within context
            ```

            Static imports:
            ```python
            import foo  # Static - imported when module loads
            from bar import baz  # Static - imported when module loads
            ```

        Returns:
            bool: True if the import is dynamic (within a control flow or scope block),
            False if it's a top-level import.
        """
        return self.parent_of_types(self.ctx.node_classes.dynamic_import_parent_types) is not None

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def set_import_module(self, new_module: str) -> None:
        """Sets the module of an import.

        Updates the module of an import statement while maintaining the import symbol. For named imports, this changes the module path that follows 'from' or is wrapped in quotes.

        Args:
            new_module (str): The new module path to import from.

        Returns:
            None

        Note:
            If the import has no module (e.g., direct imports), this method has no effect.
        """
        # TODO: if the import belongs in a multi-import statement, we need to break out the imports into individual import statements (CG-8349)
        if self.module is None:
            return

        self.module.source = new_module

    @writer
    def set_import_symbol_alias(self, new_alias: str) -> None:
        """Sets alias or name of an import at the declaration level.

        Changes the name used to refer to an imported symbol at its import declaration, either by modifying the alias if one exists,
        or the name itself if no alias is used.The change only affects the import declaration, not import usages or callsites.

        Args:
            new_alias (str): The new name to use for the imported symbol.

        Returns:
            None
        """
        if self.alias == self.symbol_name:
            self.rename(new_alias)
        else:
            for imported_usage in self.usages:
                if imported_usage.match is not None:
                    imported_usage.match.edit(new_alias)
            self.alias.source = new_alias

    def rename(self, new_name: str, priority: int = 0) -> tuple[NodeId, NodeId]:
        """Renames the import symbol and updates all its usages throughout the codebase.

        Renames both the import symbol name and any usage references to match the new name. If the import is aliased, only changes the symbol name and not the alias.

        Args:
            new_name (str): The new name to give the imported symbol.
            priority (int, optional): Priority of the rename operation. Defaults to 0.

        Returns:
            tuple[NodeId, NodeId]: A tuple containing (file_node_id, new_import_node_id).

        Note:
            For an import like 'from a.b.c import d as e', renaming with 'XYZ' will result in:
            'from a.b.c import XYZ as e'

            For an import like 'import { d as e } from 'a/b/c'', renaming with 'XYZ' will result in:
            'import { XYZ as e } from 'a/b/c''
        """
        if self.is_aliased_import():
            self.symbol_name.edit(new_name)
        else:
            super().rename(new_name, priority)

    @remover
    def remove(self, delete_formatting: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Remove this import from the import statement.

        If this import belongs to an import statement with multiple imports, removes just this single import from it.
        If this is the only import in the import statement, removes the entire import statement.

        Args:
            delete_formatting (bool, optional): Whether to delete any associated formatting. Defaults to True.
            priority (int, optional): The priority of the operation. Defaults to 0.
            dedupe (bool, optional): Whether to deduplicate imports. Defaults to True.

        Returns:
            None
        """
        import_statement = self.import_statement
        # Hack to remove the entire import statement if it only has one import
        if import_statement.imports.uncommitted_len <= 1:
            super().remove(delete_formatting=delete_formatting, priority=priority)
        else:
            # If the import belongs in a multi-import statement, remove the import specifier
            self.import_specifier.remove(delete_formatting=delete_formatting, priority=priority)

    @property
    @reader
    def import_specifier(self) -> Editable:
        """Returns the specific editable text representation of the import identifier within the
        import statement.

        Retrieves the import specifier text that appears in the actual import statement. This is the portion of text that identifies what is being imported.

        Returns:
            Editable: The editable text object representing the import specifier.
                For named imports like 'import { a as b } from 'c'', returns 'a as b'.
                For from imports like 'from a.b import c', returns 'c'.

        Raises:
            ValueError: If the subclass does not implement this property.
        """
        msg = "Subclass must implement `import_specifier`"
        raise ValueError(msg)

    @reader
    def is_reexport(self) -> bool:
        """Returns true if the Import object is also an Export object.

        Checks whether this Import node has a corresponding Export node with the same source.
        If the import is an export, it implies there are no direct usages of the import within the file it is defined in.

        Returns:
            bool: True if the import is re-exported, False otherwise.
        """
        return self.export and self.export.source == self.source

    def _removed_child_commit(self) -> None:
        self.parent.imports._removed_child_commit()

    def _removed_child(self) -> None:
        self.parent.imports._removed_child()

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        """Resolve the types used by this import."""
        # if self.is_wildcard_import():
        #     if from_file := self.from_file:
        #         yield parent.with_frame(from_file, direct=False, to_find=parent.to_find)
        #         return

        ix_seen = set()

        aliased = self.is_aliased_import()
        if imported := self._imported_symbol(resolve_exports=True):
            yield from self.with_resolution_frame(imported, direct=False, aliased=aliased)
        else:
            yield ResolutionStack(self, aliased=aliased)

    @cached_property
    @noapidoc
    @reader
    def _wildcards(self) -> dict[str, WildcardImport[Self]]:
        """A list of all imports or wildcard imports."""
        from codegen.sdk.core.file import SourceFile

        res = {}
        if self.is_wildcard_import():
            resolved = self.resolved_symbol
            if isinstance(resolved, SourceFile):
                resolved.invalidate()
                for name, symbol in resolved.valid_import_names.items():
                    res[name] = WildcardImport(self, symbol)
        return res

    @property
    @noapidoc
    def names(self) -> Generator[tuple[str, Self | WildcardImport[Self]], None, None]:
        if self.is_wildcard_import() and not self.is_aliased_import():
            if getattr(self, "_resolving_wildcards", False):
                return
            self._resolving_wildcards = True
            if self._wildcards:
                yield from self._wildcards.items()
                self._resolving_wildcards = False
                for imp in self.file.importers:
                    imp.file.invalidate()

                return
            elif self.resolved_symbol is None:
                self._resolving_wildcards = False
        yield self.name, self

    @property
    @noapidoc
    def viz(self) -> VizNode:
        return VizNode(file_path=self.filepath, start_point=self.start_point, end_point=self.end_point, name=self.name, symbol_name=self.__class__.__name__)

    @property
    @noapidoc
    def parent_symbol(self) -> Self:
        """Returns the parent symbol of the symbol."""
        return self

    @noapidoc
    @commiter
    def _compute_dependencies(self, *args, **kwargs) -> None:
        """Compute the dependencies of the export object."""
        # if self.is_wildcard_import():
        #     for _, wildcard in self._wildcards.items():
        #         for used_frame in wildcard.resolved_type_frames:
        #             if used_frame.parent_frame:
        #                 used_frame.parent_frame.add_usage(self.symbol_name or self.module, SymbolUsageType.IMPORTED_WILDCARD, self, self.ctx)
        # else:
        if isinstance(self, Import) and self.import_type == ImportType.NAMED_EXPORT:
            # It could be a wildcard import downstream, hence we have to pop the cache
            if file := self.from_file:
                file.invalidate()

        for used_frame in self.resolved_type_frames:
            if used_frame.parent_frame:
                used_frame.parent_frame.add_usage(self._unique_node, UsageKind.IMPORTED, self, self.ctx)

    @property
    def _unique_node(self):
        """A unique node for this import to identify it by"""
        # HACK: very much a hack
        return self.symbol_name or self.alias or self.module or self

    def __hash__(self):
        if self._hash is None:
            self._hash = hash((self.filepath, self.range, self.ts_node.kind_id, self._unique_node.range))
        return self._hash

    @reader
    def __eq__(self, other: object):
        if isinstance(other, Import):
            return super().__eq__(other) and self._unique_node.range == other._unique_node.range
        return super().__eq__(other)

    @noapidoc
    @reader
    def remove_if_unused(self) -> None:
        if all(
            self.transaction_manager.get_transactions_at_range(self.filepath, start_byte=usage.match.start_byte, end_byte=usage.match.end_byte, transaction_order=TransactionPriority.Remove)
            for usage in self.usages
        ):
            self.remove()

    @noapidoc
    @reader
    def resolve_attribute(self, attribute: str) -> TSourceFile | None:
        # Handles implicit namespace imports in python
        if not isinstance(self._imported_symbol(), ExternalModule):
            return None
        resolved = self.resolve_import(add_module_name=attribute)
        if resolved and (isinstance(resolved.symbol, Editable) or isinstance(resolved.from_file, Editable)):
            return resolved.symbol or resolved.from_file
        return None


TImport = TypeVar("TImport", bound="Import")


class WildcardImport(Chainable, Generic[TImport]):
    """Class to represent one of many wildcard imports."""

    imp: TImport
    symbol: Importable

    def __init__(self, imp: TImport, symbol: Importable):
        self.imp = imp
        self.symbol = symbol
        self.ts_node = imp.ts_node

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        """Resolve the types used by this import."""
        yield from self.imp.with_resolution_frame(self.symbol, direct=True)

    @noapidoc
    @reader
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        pass

    @property
    @override
    def filepath(self) -> str:
        return self.imp.filepath


class ExternalImportResolver:
    def resolve(self, imp: Import) -> str | None:
        return None
