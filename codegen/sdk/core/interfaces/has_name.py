from functools import cached_property

from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.core.expressions.defined_name import DefinedName
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.shared.decorators.docs import apidoc, noapidoc


@apidoc
class HasName:
    """An interface for any node object that has a name."""

    _name_node: Name | ChainedAttribute | DefinedName | None = None

    @cached_property
    @reader
    def name(self) -> str | None:
        """Retrieves the base name of the object without namespace prefixes.

        Returns:
            str | None: The base name of the object, or None if no name node is associated.
        """
        if isinstance(self._name_node, ChainedAttribute):
            return self._name_node.attribute.source
        return self._name_node._source if self._name_node else None

    @cached_property
    @reader
    def full_name(self) -> str | None:
        """Returns the full name of the object, including the namespace path.

        For class methods, this returns the parent class's full name followed by the method name. For chained attributes (e.g., 'a.b'), this returns the full chained name.

        Returns:
            str | None: The complete qualified name of the object. Returns None if no name is available.
        """
        if isinstance(self._name_node, ChainedAttribute):
            return self._name_node.full_name
        if isinstance(self._name_node, DefinedName):
            from codegen.sdk.core.function import Function

            if isinstance(self, Function) and self.is_method:
                return self.parent_class.full_name + "." + self.name
            # if self.parent_symbol == self or self.parent_symbol.full_name is None:
            #     return self.name
            # return self.parent_symbol.full_name + "." + self.name
        return self.name

    @reader
    def get_name(self) -> Name | ChainedAttribute | None:
        """Returns the name node of the object.

        Args:
            None

        Returns:
            Name | ChainedAttribute | None: The name node of the object. Can be a Name node for simple names,
            a ChainedAttribute for names with namespaces (e.g., a.b), or None if the object has no name.
        """
        return self._name_node

    @writer
    def set_name(self, name: str) -> None:
        """Sets the name of a code element.

        Modifies the name of the object's underlying name node. Works with both simple names and chained attributes (e.g., 'a.b').

        Args:
            name (str): The new name to set for the object.

        Returns:
            None
        """
        if self._name_node:
            self._name_node.rename_if_matching(self.name, name)

    @writer
    def rename(self, name: str) -> None:
        """Sets the name of an object and updates all its usages.

        Args:
            name (str): The new name to assign to the object.

        Returns:
            None
        """
        self.set_name(name)

    @noapidoc
    @commiter
    def _add_name_usage(self, usage_type: UsageKind):
        if name := self.get_name():
            if resolved := name.resolved_symbol():
                self._add_symbol_usages(usage_type, [resolved])
