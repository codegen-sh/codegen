from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from typing_extensions import deprecated

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.sdk.core.expressions import Expression
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.interfaces.has_value import HasValue
from codegen.sdk.core.interfaces.typeable import Typeable
from codegen.sdk.core.interfaces.usable import Usable
from codegen.sdk.extensions.autocommit import commiter
from codegen.sdk.extensions.resolution import UsageKind
from codegen.sdk.utils import find_first_descendant
from codegen.shared.decorators.docs import apidoc, noapidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.resolution_stack import ResolutionStack
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.symbol_groups.collection import Collection


logger = get_logger(__name__)

TType = TypeVar("TType", bound="Type")
Parent = TypeVar("Parent", bound="Collection[Parameter, Function]")


@apidoc
class Parameter(Usable[Parent], Typeable[TType, Parent], HasValue, Expression[Parent], Generic[TType, Parent]):
    """Abstract representation of a parameter in a Function definition."""

    _pos: int
    _name_node: Name | None = None

    def __init__(self, ts_node: TSNode, index: int, parent: Parent) -> None:
        super().__init__(ts_node, parent.file_node_id, parent.ctx, parent)
        self._pos = index
        name_node = self._get_name_node(ts_node)
        self._name_node = self._parse_expression(name_node, default=Name)
        self._init_type()
        value_node = self._get_value_node(ts_node)
        self._value_node = self._parse_expression(value_node) if value_node else None

    @reader
    def _get_name_node(self, ts_node: TSNode) -> TSNode | None:
        if ts_node.type == "identifier":
            return ts_node
        else:
            name_node = find_first_descendant(ts_node, ["identifier", "shorthand_property_identifier_pattern", "this"])
            if name_node is None:
                # Some parameters don't have names, e.g. the {} in `async run({}, arg2, arg3) {..}`
                self._log_parse("Unable to find name node in parameter: %s", ts_node.text.decode("utf-8"))
            return name_node

    @reader
    def _get_value_node(self, ts_node: TSNode) -> TSNode | None:
        return ts_node.child_by_field_name("value")

    @property
    @reader
    def index(self) -> int:
        """Returns the 0-based index of this parameter within its parent function's parameter list.

        Args:
            None

        Returns:
            int: The position of the parameter in the function's parameter list, 0-based.
        """
        return self._pos

    @deprecated("Use `type.edit` instead")
    @writer
    def set_type_annotation(self, type_annotation: str) -> None:
        """Sets the type annotation for this parameter.

        This method is deprecated in favor of `type.edit`.

        Args:
            type_annotation (str): The type annotation to set for the parameter.

        Returns:
            None
        """
        self.type.edit(type_annotation)

    @property
    @reader
    def default(self) -> str | None:
        """Returns the default value of a parameter if one exists.

        Gets the default value of a parameter in a function definition. This is the value that would be used if the parameter is not provided in a function call.

        Args:
            None

        Returns:
            str | None: The string representation of the default value if one exists, None otherwise.
        """
        default_node = self.ts_node.child_by_field_name("value")
        if default_node is None:
            return None
        return default_node.text.decode("utf-8")

    @property
    @abstractmethod
    def is_optional(self) -> bool:
        """Returns whether the parameter is optional in its function definition.

        A parameter is optional if either:
        1. It has a default value
        2. Its type annotation is Optional[T] or T | None
        3. It is variadic (*args, **kwargs)

        Returns:
            bool: True if the parameter is optional, False otherwise
        """
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)

    @property
    @abstractmethod
    def is_variadic(self) -> bool:
        """Returns whether the parameter is a variadic parameter.

        A variadic parameter allows a function to accept a variable number of arguments (e.g., *args in Python).

        Returns:
            bool: True if the parameter is variadic (can accept variable number of arguments),
                False otherwise.
        """
        msg = "Subclasses must implement this method"
        raise NotImplementedError(msg)

    @writer
    def remove(self, delete_formatting: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Removes the parameter from the function definition and all its call sites.

        Removes the parameter from a function's definition and also removes the corresponding argument
        from all call sites of the function. If an argument cannot be found at a call site, logs a message
        and continues with other call sites.

        Args:
            delete_formatting (bool, optional): Whether to delete formatting around the parameter. Defaults to True.
            priority (int, optional): Priority level for the removal operation. Defaults to 0.
            dedupe (bool, optional): Whether to deduplicate removal operations. Defaults to True.

        Returns:
            None
        """
        # Step 1: Remove all usages of the parameter in call sites
        call_sites = self.parent_function.call_sites
        for call_site in call_sites:
            arg = call_site.get_arg_by_parameter_name(self.name)
            if arg is None:
                arg = call_site.get_arg_by_index(self.index)
            if arg is None:
                logger.info(f"Unable to find argument with parameter name {self.name} at call site {call_site}")
                continue
            arg.remove(delete_formatting=delete_formatting, priority=priority, dedupe=dedupe)

        # Step 2: Actually remove the parameter from the function header
        super().remove(delete_formatting=delete_formatting, priority=priority, dedupe=dedupe)

    @writer
    def rename(self, new_name: str, priority: int = 0) -> None:
        """Renames a parameter in a function definition and updates all related references.

        Performs a comprehensive rename operation by updating the parameter name in the function definition,
        all variable usages within the function body, and any keyword arguments in call sites.

        Args:
            new_name (str): The new name for the parameter.
            priority (int, optional): The priority of the edit operation. Defaults to 0.

        Returns:
            None
        """
        # Step 1: Rename the parameter in the function definition itself
        self.set_name(new_name)

        # Step 2: Rename the parameter variable usages in the function body
        for usage in self.usages(UsageType.DIRECT):
            usage.match.edit(new_name)

        # Step 3: Rename any keyword arguments in all call sites
        parent_function = self.parent_function
        call_sites = parent_function.call_sites
        for call_site in call_sites:
            arg_to_rename = [arg for arg in call_site.args if arg.is_named and arg.name == self.name]
            for arg in arg_to_rename:
                arg.rename(new_name)

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        if self.type:
            yield from self.with_resolution_frame(self.type)
        if value := self.value:
            yield from self.with_resolution_frame(value)

    @noapidoc
    @commiter
    @override
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        if self.type:
            self.type._compute_dependencies(UsageKind.TYPE_ANNOTATION, self.parent.self_dest)
        if self.value:
            self.value._compute_dependencies(UsageKind.DEFAULT_VALUE, self.parent.self_dest)

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        ret = super().descendant_symbols
        if self.type:
            ret.extend(self.type.descendant_symbols)
        if self.value:
            ret.extend(self.value.descendant_symbols)
        return ret
