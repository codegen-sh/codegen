import itertools
from collections import defaultdict
from functools import cached_property

from tree_sitter import Range

from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.extensions.sort import sort_editables


class RangeIndex:
    _ranges: defaultdict[Range, list[Editable]]
    _canonical_range: defaultdict[Range, dict[int, Editable]]

    def __init__(self):
        self._ranges = defaultdict(list)
        self._canonical_range = defaultdict(dict)

    def add_to_range(self, editable: Editable) -> None:
        self._ranges[editable.range].append(editable)

    def mark_as_canonical(self, editable: Editable) -> None:
        self._canonical_range[editable.range][editable.ts_node.kind_id] = editable

    def get_all_for_range(self, range: Range) -> list[Editable]:
        return self._ranges[range]

    def get_canonical_for_range(self, range: Range, kind_id: int) -> Editable | None:
        if mapping := self._canonical_range.get(range, None):
            return mapping.get(kind_id, None)

    def clear(self):
        self._ranges.clear()
        self._canonical_range.clear()
        self.__dict__.pop("children", None)
        self.__dict__.pop("nodes", None)

    @cached_property
    def nodes(self) -> list[Editable]:
        return list(itertools.chain.from_iterable(self._ranges.values()))

    @cached_property
    def children(self) -> dict[Editable, list[Editable]]:
        ret = defaultdict(list)
        for node in self.nodes:
            # if node.ctx.config.debug:
            #     assert node.parent != node, node.__class__
            if node.parent != node:
                ret[node.parent].append(node)
        return ret

    def get_children(self, parent: Editable) -> list[Editable]:
        return sort_editables(self.children[parent])
