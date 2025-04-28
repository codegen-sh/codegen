from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk._proxy import proxy_property
from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.dataclasses.usage import Usage, UsageType
from codegen.sdk.core.interfaces.importable import Importable
from codegen.sdk.enums import EdgeType
from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.export import Export
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.symbol import Symbol
Parent = TypeVar("Parent", bound="Editable")


@apidoc
class Usable(Importable[Parent], Generic[Parent]):
    """An interface for any node object that can be referenced by another node."""

    @proxy_property
    @reader(cache=False)
    def symbol_usages(self, usage_types: UsageType | None = None) -> list[Import | Symbol | Export]:
        """Returns a list of symbols that use or import the exportable object.

        Args:
            usage_types (UsageType | None): The types of usages to search for. Defaults to any.

        Returns:
            list[Import | Symbol | Export]: A list of symbols that use or import the exportable object.

        Note:
            This method can be called as both a property or a method. If used as a property, it is equivalent to invoking it without arguments.
        """
        symbol_usages = []
        for usage in self.usages(usage_types=usage_types):
            symbol_usages.append(usage.usage_symbol.parent_symbol)
        return list(dict.fromkeys(symbol_usages))

    @proxy_property
    @reader(cache=False)
    def usages(self, usage_types: UsageType | None = None, max_depth: int | None = None) -> list[Usage]:
        """Returns a list of usages of the exportable object.

        Retrieves all locations where the exportable object is used in the codebase. By default, returns all usages, such as imports or references within the same file.
        When max_depth is provided:
        - At depth 1: Returns only direct usages
        - At depth > 1: Returns direct usages plus chained usages (method calls and property accesses)

        Args:
            usage_types (UsageType | None): Specifies which types of usages to include in the results. Default is any usages, or DIRECT if max_depth=1, DIRECT|CHAINED if max_depth>1.
            max_depth (int | None): Maximum depth to traverse in the usage graph. If provided, will recursively collect
                usages up to this depth. Defaults to None (only direct usages).

        Returns:
            list[Usage]: A sorted list of Usage objects representing where this exportable is used, ordered by source location in reverse.

        Raises:
            ValueError: If no usage types are specified or if only ALIASED and DIRECT types are specified together.

        Note:
            This method can be called as both a property or a method. If used as a property, it is equivalent to invoking it without arguments.
        """
        if usage_types == UsageType.DIRECT | UsageType.ALIASED:
            msg = "Combination of only Aliased and Direct usages makes no sense"
            raise ValueError(msg)

        # Default usage types based on depth
        if max_depth is not None and usage_types is None:
            if max_depth == 1:
                usage_types = UsageType.DIRECT
            else:
                usage_types = UsageType.DIRECT | UsageType.CHAINED

        assert self.node_id is not None
        usages_to_return = []
        in_edges = self.ctx.in_edges(self.node_id)
        for edge in in_edges:
            meta_data = edge[2]
            if meta_data.type == EdgeType.SYMBOL_USAGE:
                usage = meta_data.usage
                if usage_types is None or usage.usage_type in usage_types:
                    usages_to_return.append(usage)

        if max_depth is not None and max_depth > 1:
            # For max_depth > 1, recursively collect usages
            seen = set(usages_to_return)
            for usage in list(usages_to_return):  # Create a copy to iterate over
                if usage.usage_symbol and isinstance(usage.usage_symbol, Usable):
                    # When recursing, we want to find method calls and property accesses
                    next_usages = usage.usage_symbol.usages(usage_types=UsageType.CHAINED, max_depth=max_depth - 1)
                    for next_usage in next_usages:
                        if next_usage not in seen:
                            seen.add(next_usage)
                            usages_to_return.append(next_usage)

        return sorted(dict.fromkeys(usages_to_return), key=lambda x: x.match.ts_node.start_byte if x.match else x.usage_symbol.ts_node.start_byte, reverse=True)

    def rename(self, new_name: str, priority: int = 0) -> tuple[NodeId, NodeId]:
        """Renames a symbol and updates all its references in the codebase.

        Args:
            new_name (str): The new name for the symbol.
            priority (int): Priority of the edit operation. Defaults to 0.

        Returns:
            tuple[NodeId, NodeId]: A tuple containing the file node ID and the new node ID of the renamed symbol.
        """
        self.set_name(new_name)

        for usage in self.usages(UsageType.DIRECT | UsageType.INDIRECT | UsageType.CHAINED):
            usage.match.rename_if_matching(self.name, new_name)
