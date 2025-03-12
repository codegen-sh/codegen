from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, TypeVar

from codegen.sdk.core.autocommit import commiter, reader
from codegen.sdk.core.expressions import Type
from codegen.sdk.core.interfaces.supports_generic import SupportsGenerics
from codegen.sdk.enums import EdgeType

if TYPE_CHECKING:
    from collections.abc import Generator

    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.external_module import ExternalModule
    from codegen.sdk.core.interface import Interface

TType = TypeVar("TType", bound=Type)


class Inherits(SupportsGenerics, Generic[TType]):
    """This symbol inherits from other symbols."""

    @commiter
    @abstractmethod
    def compute_superclass_dependencies(self) -> None:
        pass

    @reader
    def _get_superclasses(self, max_depth: int | None = None) -> list[Class | ExternalModule | Interface]:
        """Returns a list of all classes that this class extends, up to max_depth."""
        from codegen.sdk.core.class_definition import Class
        from codegen.sdk.core.interface import Interface

        # Implements the python MRO, IE: by level
        seen = set()

        def traverse_classes(classes: list[Inherits], depth: int = 0) -> Generator[Class | Interface | ExternalModule, None, None]:
            if max_depth is not None and depth >= max_depth:
                return
            next_level = []
            for node in classes:
                for result in self.ctx.successors(node.node_id, edge_type=EdgeType.SUBCLASS):
                    if result.node_id not in seen:
                        seen.add(result.node_id)
                        yield result
                        if isinstance(result, Class) or isinstance(result, Interface):
                            next_level.append(result)
            if len(next_level) > 0:
                yield from traverse_classes(next_level, depth + 1)

        return list(traverse_classes([self]))

    @reader
    def _get_subclasses(self, max_depth: int | None = None) -> list[Class | ExternalModule | Interface]:
        """Returns a list of all classes that subclass this class, up to max_depth."""
        # Implements the python MRO, IE: by level
        seen = set()

        def traverse_classes(classes: list[Inherits], depth: int = 0) -> Generator[Class | Interface, None, None]:
            if max_depth and depth >= max_depth:
                return
            next_level = []
            for node in classes:
                for result in self.ctx.predecessors(node.node_id, edge_type=EdgeType.SUBCLASS):
                    if result.node_id not in seen:
                        seen.add(result.node_id)
                        yield result
                        next_level.append(result)
            if len(next_level) > 0:
                yield from traverse_classes(next_level, depth + 1)

        return list(traverse_classes([self]))
