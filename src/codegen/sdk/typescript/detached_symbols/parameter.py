from __future__ import annotations

from typing import TYPE_CHECKING, override

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.autocommit.decorators import writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.detached_symbols.parameter import Parameter
from codegen.sdk.core.expressions.union_type import UnionType
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.extensions.autocommit import commiter
from codegen.sdk.typescript.expressions.object_type import TSObjectType
from codegen.sdk.typescript.expressions.type import TSType
from codegen.sdk.typescript.symbol_groups.dict import TSPair
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.placeholder.placeholder import Placeholder
    from codegen.sdk.typescript.function import TSFunction


@ts_apidoc
class TSParameter(Parameter[TSType, Collection["TSParameter", "TSFunction"]]):
    """A class representing a TypeScript function parameter with extensive type analysis capabilities.

    This class provides functionality to inspect and manipulate TypeScript function parameters,
    including support for destructured parameters, optional parameters, variadic parameters,
    default values, and type annotations.

    Attributes:
        type (TSType): The TypeScript type annotation of the parameter.
    """

    def __init__(self, ts_node: TSNode, index: int, parent: TSFunction, type: TSType | Placeholder | None = None) -> None:
        super().__init__(ts_node, index, parent)
        if not self.type and type is not None:
            self.type = type  # Destructured types

    @property
    @reader
    def is_destructured(self) -> bool:
        """Determines if a parameter is part of an object destructuring pattern.

        Checks the parameter's tree-sitter node type to determine if it represents a destructured parameter.
        A parameter is considered destructured if it appears within an object destructuring pattern.

        Returns:
            bool: True if the parameter is destructured, False otherwise.
        """
        return self.ts_node.type in ("shorthand_property_identifier_pattern", "object_assignment_pattern")

    @property
    @reader
    def is_optional(self) -> bool:
        """Determines if a parameter is marked as optional in TypeScript.

        Checks whether a parameter is marked with the '?' syntax in TypeScript, indicating that it is optional.
        If the parameter is part of a destructured pattern, this function returns False as optionality is
        handled at the function level for destructured parameters.

        Returns:
            bool: True if the parameter is marked as optional, False otherwise.
        """
        if self.is_destructured:
            # In this case, individual destructured parameters are not marked as optional
            # The entire object might be optional, but that's handled at the function level
            return False
        else:
            return self.ts_node.type == "optional_parameter"

    @property
    @reader
    def is_variadic(self) -> bool:
        """Determines if a parameter is variadic (using the rest operator).

        A property that checks if the parameter uses the rest pattern (e.g., ...args in TypeScript),
        which allows the parameter to accept an arbitrary number of arguments.

        Returns:
            bool: True if the parameter is variadic (uses rest pattern), False otherwise.
        """
        pattern = self.ts_node.child_by_field_name("pattern")
        return pattern is not None and pattern.type == "rest_pattern"

    @property
    @reader
    def default(self) -> str | None:
        """Returns the default value of a parameter.

        Retrieves the default value of a parameter, handling both destructured and non-destructured parameters.
        For destructured parameters, returns the default value if it's an object assignment pattern.
        For non-destructured parameters, returns the value specified after the '=' sign.

        Returns:
            str | None: The default value of the parameter as a string if it exists, None otherwise.
        """
        # =====[ Destructured ]=====
        if self.is_destructured:
            if self.ts_node.type == "object_assignment_pattern":
                return self.ts_node.children[-1].text.decode("utf-8")
            else:
                return None

        # =====[ Not destructured ]=====
        default_node = self.ts_node.child_by_field_name("value")
        if default_node is None:
            return None
        return default_node.text.decode("utf-8")

    @noapidoc
    @commiter
    @override
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        if self.type:
            if not (self.is_destructured and self.index > 0):
                self.type._compute_dependencies(UsageKind.TYPE_ANNOTATION, dest or self.parent.self_dest)
        if self.value:
            self.value._compute_dependencies(UsageKind.DEFAULT_VALUE, dest or self.parent.self_dest)

    @writer
    def convert_to_interface(self) -> None:
        """Converts a parameter's inline type definition to an interface.

        For React components, converts inline props type definitions to a separate interface.
        Handles both simple types and complex types including generics, extends patterns, and union types.
        The interface will be named {ComponentName}Props and inserted before the component.
        Supports extracting types from destructured parameters and preserves any type parameters.

        Example:
            ```typescript
            // Before
            function Button(props: { text: string, onClick: () => void }) {
                return <button>{props.text}</button>;
            }

            // After
            interface ButtonProps {
                text: string;
                onClick: () => void;
            }
            function Button(props: ButtonProps) {
                return <button>{props.text}</button>;
            }
            ```
        """
        if not self.type or not self.parent_function.is_jsx or not isinstance(self.type, TSObjectType | UnionType):
            return

        # # Get the type definition and component name
        # type_def = self.type.source
        component_name = self.parent_function.name

        # # Handle extends pattern
        extends_clause: str = ""

        type = self.type
        if isinstance(type, UnionType):
            for subtype in type:
                if isinstance(subtype, TSObjectType):
                    type = subtype
                else:
                    extends_clause += f" extends {subtype.source}"

        # # Extract generic type parameters if present
        generic_params = ""
        if self.parent_function.type_parameters:
            generic_params = self.parent_function.type_parameters.source
        interface_name = f"{component_name}Props"
        # # Update parameter type to use interface
        if generic_params:
            interface_name += generic_params

        # # Convert type definition to interface
        interface_def = f"interface {interface_name}{extends_clause} {{\n"

        # Strip outer braces and convert to semicolon-separated lines
        for value in type.values():
            interface_def += f"    {value.parent_of_type(TSPair).source.rstrip(',')};\n"
        interface_def += "}"

        # Insert interface before the function
        self.parent_function.insert_before(interface_def + "\n")

        self.type.edit(interface_name)
