from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Generic, TypeVar, override

from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.expressions import Expression, Value
from codegen.sdk.core.expressions.name import Name
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.extensions.autocommit import commiter
from codegen.sdk.typescript.detached_symbols.jsx.prop import JSXProp
from codegen.sdk.utils import find_all_descendants
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.dataclasses.usage import UsageKind
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.typescript.detached_symbols.jsx.expression import JSXExpression

Parent = TypeVar("Parent", bound="Editable")


@ts_apidoc
class JSXElement(Expression[Parent], HasName, Generic[Parent]):
    """Abstract representation of TSX/JSX elements, e.g. `<MyComponent />`. This allows for many React-specific modifications, like adding props, changing the name, etc."""

    _name_node: Name | None

    def __init__(self, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None:
        super().__init__(ts_node, file_node_id, ctx, parent)
        open_tag = self.ts_node.child_by_field_name("open_tag") or self.ts_node
        name_node = open_tag.child_by_field_name("name")
        self._name_node = self._parse_expression(name_node, default=Name)
        self.children  # Force parse children of this JSX element

    @cached_property
    @reader
    def jsx_elements(self) -> list[JSXElement]:
        """Returns a list of JSX elements nested within the current element.

        Gets all JSX elements that are descendants of this element in the syntax tree, excluding the element itself.
        This includes both regular JSX elements (`<Tag>...</Tag>`) and self-closing elements (`<Tag />`).

        Args:
            None

        Returns:
            list[JSXElement]: A list of JSXElement objects representing all nested JSX elements.
        """
        jsx_elements = []
        for node in self.extended_nodes:
            jsx_element_nodes = find_all_descendants(node.ts_node, {"jsx_element", "jsx_self_closing_element"})
            jsx_elements.extend([self._parse_expression(x) for x in jsx_element_nodes if x != self.ts_node])
        return jsx_elements

    @cached_property
    @reader
    def expressions(self) -> list[JSXExpression]:
        """Gets all JSX expressions within the JSX element.

        Retrieves all JSX expressions that are descendant nodes of the current JSX element, including expressions in child elements and attributes.

        Returns:
            list[JSXExpression]: A list of JSX expression objects found within this element, excluding the current element itself.
        """
        jsx_expressions = []
        for node in self.extended_nodes:
            jsx_expressions_nodes = find_all_descendants(node.ts_node, {"jsx_expression"})
            jsx_expressions.extend([self._parse_expression(x) for x in jsx_expressions_nodes if x != self.ts_node])
        return jsx_expressions

    @property
    @noapidoc
    @reader
    def _attribute_nodes(self) -> list[Editable]:
        """Returns all attribute nodes of the element"""
        open_tag = self.ts_node.child_by_field_name("open_tag") or self.ts_node
        attribute_nodes = open_tag.children_by_field_name("attribute")
        return [Value(x, self.file_node_id, self.ctx, self) for x in attribute_nodes]

    @property
    @reader
    def props(self) -> list[JSXProp]:
        """Retrieves all JSXProps (attributes) from a JSX element.

        Gets all props (attributes) on the current JSX element. For example, in `<MyComponent prop1="value" />`, this would return a list with one JSXProp object representing `prop1="value"`.

        Args:
            self: The JSXElement instance.

        Returns:
            list[JSXProp]: A list of JSXProp objects representing each attribute on the element.
        """
        return [self._parse_expression(x.ts_node, default=JSXProp) for x in self._attribute_nodes]

    @reader
    def get_prop(self, name: str) -> JSXProp | None:
        """Returns the JSXProp with the given name from the JSXElement.

        Searches through the element's props to find a prop with a matching name.

        Args:
            name (str): The name of the prop to find.

        Returns:
            JSXProp | None: The matching JSXProp object if found, None if not found.
        """
        for prop in self.props:
            if prop.name == name:
                return prop
        return None

    @property
    def attributes(self) -> list[JSXProp]:
        """Returns all JSXProp on this JSXElement, an alias for JSXElement.props.

        Returns all JSXProp attributes (props) on this JSXElement. For example, for a JSX element like
        `<MyComponent prop1="value" />`, this would return a list containing one JSXProp object.

        Returns:
            list[JSXProp]: A list of JSXProp objects representing each attribute/prop on the JSXElement.
        """
        return [self._parse_expression(x.ts_node, default=JSXProp) for x in self._attribute_nodes]

    @writer
    def set_name(self, name: str) -> None:
        """Sets the name of a JSXElement by modifying both opening and closing tags.

        Updates the name of a JSX element, affecting both self-closing tags (`<Tag />`) and elements with closing tags (`<Tag></Tag>`).

        Args:
            name (str): The new name to set for the JSX element.

        Returns:
            None: The method modifies the JSXElement in place.
        """
        # This should correctly set the name of both the opening and closing tags
        if open_tag := self.ts_node.child_by_field_name("open_tag"):
            name_node = self._parse_expression(open_tag.child_by_field_name("name"), default=Name)
            name_node.edit(name)
            if close_tag := self.ts_node.child_by_field_name("close_tag"):
                name_node = self._parse_expression(close_tag.child_by_field_name("name"), default=Name)
                name_node.edit(name)
        else:
            # If the element is self-closing, we only need to edit the name of the element
            super().set_name(name)

    @writer
    def add_prop(self, prop_name: str, prop_value: str) -> None:
        """Adds a new prop to a JSXElement.

        Adds a prop with the specified name and value to the JSXElement. If the element already has props,
        the new prop is added after the last existing prop. If the element has no props, the new prop is
        added immediately after the element name.

        Args:
            prop_name (str): The name of the prop to add.
            prop_value (str): The value of the prop to add.

        Returns:
            None
        """
        if len(self.props) > 0:
            last_prop = self.props[-1]
            # Extra padding is handled by the insert_after method on prop
            last_prop.insert_after(f"{prop_name}={prop_value}", newline=False)
        else:
            self._name_node.insert_after(f" {prop_name}={prop_value}", newline=False)

    @property
    @reader
    @noapidoc
    def _source(self):
        """Text representation of the Editable instance"""
        return self.ts_node.text.decode("utf-8").strip()

    @writer
    def wrap(self, opening_tag: str, closing_tag: str) -> None:
        """Wraps the current JSXElement with the provided opening and closing tags, properly handling indentation.

        Args:
            opening_tag (str): The opening JSX tag to wrap around the current element (e.g. `<div prop={value}>`)
            closing_tag (str): The closing JSX tag to wrap around the current element (e.g. `</div>`)
        """
        current_source = self.source
        indented_source = "\n".join(f"  {line.rstrip()}" for line in current_source.split("\n"))
        new_source = f"{opening_tag}\n{indented_source}\n{closing_tag}"
        self.edit(new_source, fix_indentation=True)

    @commiter
    @noapidoc
    @override
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        for node in self.children:
            node._compute_dependencies(usage_type, dest=dest)
