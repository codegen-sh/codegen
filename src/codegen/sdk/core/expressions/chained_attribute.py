from collections.abc import Generator
from typing import TYPE_CHECKING, Generic, Optional, Self, TypeVar, override

from tree_sitter import Node as TSNode

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions import Name
from codegen.sdk.core.expressions.expression import Expression
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.core.interfaces.resolvable import Resolvable
from codegen.sdk.extensions.autocommit import commiter
from codegen.shared.decorators.docs import apidoc, noapidoc

if TYPE_CHECKING:
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable


Object = TypeVar("Object", bound="Chainable")
Attribute = TypeVar("Attribute", bound="Resolvable")
Parent = TypeVar("Parent", bound="Expression")


@apidoc
class ChainedAttribute(Expression[Parent], Resolvable, Generic[Object, Attribute, Parent]):
    """An attribute of an object. (IE a method on a class, a function from a module, etc)

    Examples:
     A.method()
    """

    _object: Object
    _attribute: Attribute

    def __init__(self, ts_node, file_node_id, ctx, parent: Parent, object: TSNode, attribute: TSNode):
        super().__init__(ts_node, file_node_id, ctx, parent=parent)
        self._object = self._parse_expression(object, default=Name)
        if self.ctx.parser._should_log:
            if not isinstance(self._object, Chainable):
                msg = f"{self._object.__class__} is not chainable: {self._object.source}\nfile: {self.filepath}"
                raise ValueError(msg)
        self._attribute = self._parse_expression(attribute, default=Name)
        if self.ctx.parser._should_log:
            if not isinstance(self._attribute, Resolvable):
                msg = f"{self._attribute.__class__} is not resolvable: {self._attribute.source}\nfile: {self.filepath}"
                raise ValueError(msg)

    @property
    @reader
    def full_name(self) -> str:
        """Returns the full name of the attribute, including the object expression.

        Gets the complete name representation of a chained attribute, which includes both the object and attribute parts (e.g., 'my_object.my_attribute').

        Returns:
            str: The full string representation of the chained attribute expression.
        """
        return self.source

    @property
    @reader
    def attribute(self) -> Attribute:
        """Gets the attribute being accessed in a chained attribute expression.

        This property returns the Attribute component of a chained attribute expression (e.g., in `object.attribute`, returns the `attribute` part).

        Args:
            None

        Returns:
            Attribute: The attribute component of the chained expression.
        """
        return self._attribute

    @property
    @reader
    def attribute_chain(self) -> list["FunctionCall | Name"]:
        """Returns a list of elements in a chained attribute expression.

        Breaks down chained expressions into individual components in order of appearance.
        For example: `a.b.c().d` -> [Name("a"), Name("b"), FunctionCall("c"), Name("d")]

        Returns:
            list[FunctionCall | Name]: List of Name nodes (property access) and FunctionCall nodes (method calls)
        """
        from codegen.sdk.core.detached_symbols.function_call import FunctionCall

        ret = []
        curr = self

        # Traverse backwards in code (children of tree node)
        while isinstance(curr, ChainedAttribute):
            curr = curr.object

            if isinstance(curr, FunctionCall):
                ret.insert(0, curr)
                curr = curr.get_name()
            elif isinstance(curr, ChainedAttribute):
                ret.insert(0, curr.attribute)

            # This means that we have reached the base of the chain and the first item was an attribute (i.e a.b.c.func())
            if isinstance(curr, Name) and not isinstance(curr.parent, FunctionCall):
                ret.insert(0, curr)

        curr = self

        # Traversing forward in code (parents of tree node). Will add the current node as well
        while isinstance(curr, ChainedAttribute) or isinstance(curr, FunctionCall):
            if isinstance(curr, FunctionCall):
                ret.append(curr)
            elif isinstance(curr, ChainedAttribute) and not isinstance(curr.parent, FunctionCall):
                ret.append(curr.attribute)

            curr = curr.parent

        return ret

    @property
    def object(self) -> Object:
        """Returns the object that contains the attribute being looked up.

        Provides access to the object part of a chained attribute expression (e.g., in 'A.method', returns the 'A' part).

        Returns:
            Object: The object component of the chained attribute expression. Guaranteed to be an instance of Chainable.
        """
        return self._object

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        from codegen.sdk.typescript.namespace import TSNamespace

        if not self.ctx.config.method_usages:
            return
        if res := self.file.valid_import_names.get(self.full_name, None):
            # Module imports
            yield from self.with_resolution_frame(res)
            return
        # HACK: This is a hack to skip the resolved types for namespaces
        if isinstance(self.object, TSNamespace):
            return
        for resolved_type in self.object.resolved_type_frames:
            top = resolved_type.top
            if not isinstance(top.node, HasAttribute):
                generics: dict = resolved_type.generics.copy()
                if top.node.source.lower() == "dict" and self.attribute.source in ("values", "get", "pop"):
                    if len(generics) == 2:
                        generics.pop(next(iter(generics.keys())))
                yield from self.with_resolution_frame(top.node, generics=generics, direct=resolved_type.is_direct_usage, chained=True)
                self._log_parse("%r does not have attributes, passing %s generics", top.node, len(generics))
                continue
            name = self.attribute.source
            if attr := top.node.resolve_attribute(name):
                yield from self.with_resolution_frame(attr, chained=True, generics=resolved_type.generics)
            else:
                self._log_parse("Couldn't resolve attribute %s on %s", name, top.node)
                yield from self.with_resolution_frame(top.node, direct=resolved_type.is_direct_usage, chained=True)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind, dest: Optional["HasName | None"] = None) -> None:
        edges = []
        for used_frame in self.resolved_type_frames:
            edges.extend(used_frame.get_edges(self, usage_type, dest, self.ctx))
        edges = list(dict.fromkeys(edges))
        self.ctx.add_edges(edges)
        if self.object.source not in ("self", "this"):
            self.object._compute_dependencies(usage_type, dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list["Importable"]:
        return self.object.descendant_symbols + self.attribute.descendant_symbols

    @noapidoc
    @writer
    def rename_if_matching(self, old: str, new: str):
        if self.attribute.source == old:
            self.attribute.edit(new)
