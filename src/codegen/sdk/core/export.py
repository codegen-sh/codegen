from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, Self, TypeVar

from codegen.sdk.core.interfaces.exportable import Exportable
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.export_statement import ExportStatement
    from codegen.sdk.core.symbol_groups.collection import Collection


Parent = TypeVar("Parent", bound="Collection[Export, ExportStatement]")


@apidoc
class Export(Exportable[Parent], Generic[Parent]):
    """Represents a single symbol being exported.

    Attributes:
        export_statement: The statement representing the export.
    """

    export_statement: ExportStatement

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None:
        self.to_file_id = file_node_id
        super().__init__(ts_node=ts_node, file_node_id=file_node_id, ctx=ctx, parent=parent)

    @noapidoc
    @abstractmethod
    def parse(self, ctx: CodebaseContext) -> None:
        """Add self to the graph and SYMBOL_USAGE edges from export to exported symbol."""

    @property
    @abstractmethod
    def exported_symbol(self) -> Exportable | None:
        """Returns the symbol, file, or import being exported from this export object.

        Returns:
            Exportable | None: The exported symbol, file, or import, or None if it cannot be resolved.
        """

    @property
    @abstractmethod
    def resolved_symbol(self) -> Exportable | None:
        """Returns the resolved symbol for an export.

        Gets the final symbol, file, or external module that this export resolves to by following through indirect imports and exports.

        Returns:
            Exportable | None: The final resolved symbol, which can be a Symbol, File, or External module. Returns None if the symbol cannot be resolved.
        """

    @abstractmethod
    def is_named_export(self) -> bool:
        """Determines if the export is named or default.

        Returns:
            bool: True if the export is named, False if it is default.
        """

    @abstractmethod
    def is_module_export(self) -> bool:
        """Determines if the export is a module-level export.

        This method checks if the export statement represents a module-level export,
        such as wildcard exports or default object exports.

        Returns:
            bool: True if the export is a module-level export, False otherwise.
        """

    def is_aliased(self) -> bool:
        """Determines if the Export object is aliased.

        Checks if the exported symbol has a different name than the name it is exported as.

        Returns:
            bool: True if the exported symbol has a different name than the name it is exported as, False otherwise.
        """
        from codegen.sdk.core.import_resolution import Import

        if self.exported_symbol is None:
            return False
        if isinstance(self.exported_symbol, Import):
            return self.exported_name != self.exported_symbol.symbol_name
        return self.exported_name != self.exported_symbol.name

    @noapidoc
    @commiter
    def compute_export_dependencies(self) -> None:
        raise NotImplementedError

    @property
    @noapidoc
    def parent_symbol(self) -> Self:
        """Returns the parent symbol of the symbol."""
        return self
