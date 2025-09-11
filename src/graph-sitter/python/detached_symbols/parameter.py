from typing_extensions import deprecated

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.detached_symbols.parameter import Parameter
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.python.expressions.type import PyType
from codegen.sdk.shared.decorators.docs import py_apidoc


@py_apidoc
class PyParameter(Parameter[PyType, Collection["PyParameter", "PyFunction"]]):
    """Extends Parameter for Python codebases."""

    @property
    @reader
    def is_optional(self) -> bool:
        """Determines if the parameter is optional in Python code.

        A parameter is considered optional if it has a default value or if it is a list/dictionary splat pattern.
        This includes default parameters, typed default parameters, and list/dictionary splat patterns.

        Returns:
            bool: True if the parameter is optional, False otherwise.
        """
        return (
            self.ts_node.type == "default_parameter" or self.ts_node.type == "typed_default_parameter" or self.ts_node.type == "list_splat_pattern" or self.ts_node.type == "dictionary_splat_pattern"
        )

    @property
    @reader
    def is_variadic(self) -> bool:
        """Determines if a parameter is a variadic parameter.

        Checks if this parameter is defined as a variadic parameter using the splat operator (*args or **kwargs).

        Returns:
            bool: True if the parameter is variadic (uses * or ** syntax), False otherwise.
        """
        return self.ts_node.type == "list_splat_pattern" or self.ts_node.type == "dictionary_splat_pattern"

    @deprecated("Use `type.edit` instead")
    @writer
    def set_type_annotation(self, type_annotation: str, include_comment: str = "") -> None:
        """Sets the type annotation of a parameter.

        Sets or updates the type annotation for this parameter. This method is deprecated in favor of using `type.edit` directly.

        Args:
            type_annotation (str): The type annotation to set for the parameter.
            include_comment (str, optional): A comment to include with the type annotation. Defaults to "".

        Returns:
            None

        Deprecated:
            Use `type.edit` instead.
        """
        self.type.edit(type_annotation)

    @writer
    def add_trailing_comment(self, comment: str) -> None:
        """Add a trailing comment to a parameter in a function signature.

        Adds a trailing comment after the specified parameter in the parent function's signature, followed by a newline.

        Args:
            comment (str): The comment text to be added after the parameter.

        Returns:
            None
        """
        self.parent_function.edit(self.parent_function.source.replace(self.source + ",", self.source + "," + f"#  {comment} \n\n"))
