from abc import ABC, abstractmethod
from functools import cached_property

from tree_sitter import Node as TSNode

from codegen.sdk._proxy import ProxyProperty
from codegen.sdk.codebase.span import Span
from codegen.sdk.output.inspect import is_noapidoc, only_default_args
from codegen.sdk.output.placeholder import Placeholder
from codegen.sdk.output.utils import safe_getattr
from codegen.sdk.shared.decorators.docs import noapidoc
from codegen.sdk.types import JSON

BLACKLIST = ["json", "G", "viz", "autocommit_cache", "ts_node", "symbol_usages", "usages"]


@noapidoc
class JSONable(ABC):
    ts_node: TSNode

    @noapidoc
    def _list_members(self, include_methods: bool = True) -> dict[str, object]:
        """Lists all valid members (properties/attributes/methods) of this object."""
        members = {}
        for attr in dir(self):
            if attr in BLACKLIST or attr.startswith("_"):
                continue
            if is_noapidoc(self, attr):
                continue
            val = safe_getattr(self, attr, None)
            if val is None:
                continue
            if callable(val) and not isinstance(val, ProxyProperty):
                if not include_methods:
                    continue
                if not safe_getattr(val, "_apidoc", True):
                    continue
                if safe_getattr(val, "_reader", False):
                    if not only_default_args(val):
                        continue
                    attr += "()"
                    val = val()
            members[attr] = val
        return members

    @noapidoc
    def json(self, max_depth: int = 2, methods: bool = True) -> JSON:
        if max_depth < 0:
            self._add_to_index
            return self.placeholder.model_dump()

        res = {}
        for attr, val in self._list_members(include_methods=methods).items():
            depth = max_depth - 1

            if isinstance(val, JSONable):
                val = val.json(depth, methods)
            if isinstance(val, list):
                val = [elem.json(depth, methods) if isinstance(elem, JSONable) else elem for elem in val]
            if isinstance(val, dict):
                val = {key: elem.json(depth, methods) if isinstance(elem, JSONable) else elem for key, elem in val.items()}
            if isinstance(val, dict | str | list | int | float | bool | None):
                res[attr] = val

        return res

    @property
    @noapidoc
    def placeholder(self) -> Placeholder:
        """Property that returns a placeholder representation of the current object.

        Creates a Placeholder object representing the current object, typically when a full JSON
        representation cannot be provided due to depth limitations.

        Returns:
            Placeholder: A simplified representation containing the object's span, string representation,
                kind_id from the TreeSitter node, and class name.
        """
        return Placeholder(span=self.span, preview=repr(self), kind_id=self.ts_node.kind_id, name=self.__class__.__name__)

    @property
    @abstractmethod
    @noapidoc
    def span(self) -> Span: ...
    @cached_property
    @abstractmethod
    @noapidoc
    def _add_to_index(self) -> None: ...
