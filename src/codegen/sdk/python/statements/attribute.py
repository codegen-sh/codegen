from typing import TYPE_CHECKING, Self

from tree_sitter import Node as TSNode

from codegen.sdk._proxy import proxy_property
from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.statements.attribute import Attribute
from codegen.sdk.python.assignment import PyAssignment
from codegen.sdk.python.statements.assignment_statement import PyAssignmentStatement
from codegen.sdk.shared.decorators.docs import noapidoc, py_apidoc
from codegen.sdk.shared.exceptions.api import APINotApplicableForLanguageError

if TYPE_CHECKING:
    from codegen.sdk.python.class_definition import PyClass


@py_apidoc
class PyAttribute(Attribute["PyCodeBlock", "PyAssignment"], PyAssignmentStatement):
    """Python implementation of Attribute detached symbol."""

    @reader
    def _parse_assignment(self, assignment_node: TSNode | None = None) -> PyAssignment:
        """Parses the assignment in the expression"""
        if not assignment_node:
            assignment_node = next(x for x in self.ts_node.named_children if x.type == "assignment")
        return self._parse_expression(assignment_node)

    @reader
    def _get_name_node(self) -> TSNode:
        """Returns the ID node from the root node of the symbol"""
        assignment_node = next(x for x in self.ts_node.named_children if x.type == "assignment")
        return assignment_node.child_by_field_name("left")

    @property
    @reader
    def is_private(self) -> bool:
        """Determines if this attribute is private by checking if its name starts with an underscore.

        Args:
            None

        Returns:
            bool: True if the attribute name starts with an underscore, False otherwise.
        """
        return self.name.startswith("_")

    @proxy_property
    @reader
    def local_usages(self) -> list[Editable[Self]]:
        """Returns all instances where this attribute is used within its parent code block.

        Finds all references to this attribute that are prefixed with 'self.' within the code block, excluding the initial assignment.

        Note:
        This method can be called as both a property or a method. If used as a property, it is equivalent to invoking it without arguments.

        Returns:
            list[Editable[Self]]: A sorted list of unique attribute references. Each reference is an Editable object representing a usage of this attribute.
        """
        usages = []
        for statement in self.parent.statements:
            var_references = statement.find(f"self.{self.name}", exact=True)
            for var_reference in var_references:
                # Exclude the variable usage in the assignment itself
                if self.ts_node.byte_range[0] <= var_reference.ts_node.start_byte and self.ts_node.byte_range[1] >= var_reference.ts_node.end_byte:
                    continue
                usages.append(var_reference)
        return sorted(dict.fromkeys(usages), key=lambda x: x.ts_node.start_byte)

    @property
    def is_optional(self) -> bool:
        """Check if the attribute is optional.

        Returns `True` if the attribute is marked as optional, `False` otherwise. Not applicable for Python and will raise an error.

        Returns:
            bool: Whether the attribute is optional.

        Raises:
            APINotApplicableForLanguageError: Always raised as Python does not have explicit optional attribute syntax.
        """
        msg = "Python doesn't have an explicit syntax for optional attributes"
        raise APINotApplicableForLanguageError(msg)

    @property
    @reader
    @noapidoc
    def attribute_docstring(self) -> str:
        """Definition of the attribute. Ex: `type: TType`"""
        attr_def_source = f"{self.name}"
        if self.assignment.type:
            attr_def_source += ": " + self.assignment.type.source
        return attr_def_source

    @noapidoc
    @reader
    def docstring(self, base_class: "PyClass") -> str | None:
        """Parse the docstring of the attribute from it's parent class docstrings."""
        from codegen.sdk.python.class_definition import PyClass

        to_search = [base_class]
        to_search.extend(base_class.superclasses())
        for superclass in to_search:
            if isinstance(superclass, PyClass):
                if docstring := superclass.docstring:
                    parsed = docstring.parse()
                    for param in parsed.params:
                        if param.arg_name == self.name:
                            return param.description
        return None
