from __future__ import annotations

import os
from typing import TYPE_CHECKING, Self

from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.generic_type import GenericType
from codegen.sdk.core.expressions.placeholder_type import PlaceholderType
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.symbol_group import SymbolGroup
from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection
from codegen.sdk.core.symbol_groups.parents import Parents
from codegen.sdk.typescript.detached_symbols.decorator import TSDecorator
from codegen.sdk.typescript.detached_symbols.parameter import TSParameter
from codegen.sdk.typescript.expressions.type import TSType
from codegen.sdk.typescript.function import TSFunction
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.shared.decorators.docs import noapidoc, ts_apidoc

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.symbol_statement import SymbolStatement
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock


@ts_apidoc
class TSClass(Class[TSFunction, TSDecorator, "TSCodeBlock", TSParameter, TSType], TSHasBlock, TSSymbol):
    """A class representing a TypeScript/JavaScript class with enhanced functionality for class manipulation.

    The TSClass provides comprehensive functionality for working with TypeScript/JavaScript classes,
    including handling class methods, attributes, JSX components, and inheritance relationships.
    It supports operations like adding source code to class bodies, managing class attributes,
    and handling React JSX components.

    Attributes:
        parent_classes (Parents | None): The parent classes that this class extends or implements.
        constructor_keyword (str): The keyword used to identify the constructor method.
    """

    constructor_keyword = "constructor"
    """
    Representation of a Class in JavaScript/TypeScript
    """

    def __init__(self, ts_node: TSNode, file_id: NodeId, ctx: CodebaseContext, parent: SymbolStatement) -> None:
        super().__init__(ts_node, file_id, ctx, parent)
        if superclasses_node := self.child_by_field_types("class_heritage"):
            if extends_clause := superclasses_node.child_by_field_types(["extends_clause", "implements_clause"]):
                self.parent_classes = Parents(extends_clause.ts_node, self.file_node_id, self.ctx, self)
        if self.constructor is not None and len(self.constructor.parameters) > 0:
            self._parameters = SymbolGroup(self.file_node_id, self.ctx, self, children=self.constructor.parameters)
        self.type_parameters = self.child_by_field_name("type_parameters")

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        """Adds an internal edge from itself to used symbol references within itself."""
        dest = dest or self.self_dest
        # =====[ SUBCLASSING ]=====
        if self.parent_classes is not None:
            self.parent_classes._compute_dependencies(UsageKind.SUBCLASS, dest)

        if self.type_parameters:
            self.type_parameters._compute_dependencies(UsageKind.GENERIC, dest)
        # =====[ BODY IDENTIFIERS ]=====
        # TODO - this breaks if there's a local variable that shadows a global variable... tough
        self.code_block._compute_dependencies(usage_type, dest)

    @staticmethod
    @noapidoc
    def _get_name_node(ts_node: TSNode) -> TSNode | None:
        """Returns the ID node from the root node of the symbol"""
        if ts_node.parent and ts_node.parent.type == "pair":
            return ts_node.parent.child_by_field_name("key")
        return ts_node.child_by_field_name("name")

    @reader
    def _parse_methods(self) -> MultiLineCollection[TSFunction, Self]:
        methods = [m.symbol for m in self.code_block.symbol_statements if isinstance(m.symbol, TSFunction)]
        block_node = self.code_block.ts_node
        if len(block_node.children) == 2:
            # If the class definition is an empty class, there is no indent
            indent_size = 0
        else:
            # Otherwise, the indent should match the first line that appears in the code block
            indent_size = block_node.children[1].start_point[1]
        if len(methods) > 0:
            start_byte = methods[0].start_byte - methods[0].start_point[1]
        elif len(self.code_block.statements) > 0:
            start_byte = self.code_block.statements[-1].ts_node.end_byte + 2
        else:
            start_byte = block_node.start_byte - block_node.start_point[1]
        return MultiLineCollection(
            children=methods, file_node_id=self.file_node_id, ctx=self.ctx, parent=self, node=self.code_block.ts_node, indent_size=indent_size, start_byte=start_byte, end_byte=block_node.end_byte - 1
        )

    @property
    @reader
    def is_jsx(self) -> bool:
        """Determine if the class is a React JSX component.

        Check if any parent class contains 'React' in its name or source.

        Returns:
            bool: True if the class inherits from a React component, False otherwise.
        """
        if self.parent_classes is None:
            return False

        for p in self.parent_classes:
            if isinstance(p, HasName):
                if "React" in p.full_name:
                    return True
            elif isinstance(p, PlaceholderType):
                if "React" in p.source:
                    return True
            for resolution in p.resolved_types:
                if isinstance(resolution, ExternalModule):
                    if "react" in resolution.source:
                        return True
        return False

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def add_source(self, source: str) -> None:
        """Adds source code to a class body.

        Adds a block of source code to the class body. The code will be added at the end of the existing code block,
        maintaining proper indentation based on the class's structure.

        Args:
            source (str): The source code to be added to the class body.

        Returns:
            None
        """
        msg = "TODO"
        raise NotImplementedError(msg)

    @writer
    def add_attribute_from_source(self, source: str) -> None:
        """Adds a class attribute from source code to a TypeScript/JavaScript class.

        Adds the attribute to the class in a suitable location based on the class's current structure:
        after existing attributes if any exist, before methods if any exist, or in an empty class block.

        Args:
            source (str): The source code of the attribute to add to the class.

        Returns:
            None
        """
        attributes = self.attributes
        if len(attributes) > 0:
            last_attribute = attributes[-1]
            semi_colon = last_attribute.next_sibling
            indent = " " * last_attribute.start_point[1]
            semi_colon.insert_after(f"{indent}{source}", fix_indentation=False)
        elif (methods := self.methods) and len(methods) > 0:
            first_method = methods[0]
            first_method.insert_before(f"{source}\n", fix_indentation=True)
        else:
            indent = " " * (4 * self.code_block.level)
            self.code_block.edit(f"{{\n{indent}{source}\n}}", fix_indentation=False)

    def convert_props_to_interface(self) -> None:
        """Converts React component props to TypeScript interfaces.

        For React class components, converts PropTypes declarations to a separate interface.
        The interface will be named {ComponentName}Props and inserted before the component.
        The component will be updated to extend React.Component with the interface type parameter.

        Handles both simple types and complex types including:
        - PropTypes declarations
        - Union types and optional props
        - Nested object shapes
        - Arrays and complex types
        - Required vs optional props

        Example:
            ```typescript
            // Before
            class Button extends React.Component {
                render() {
                    return <button onClick={this.props.onClick}>{this.props.text}</button>;
                }
            }
            Button.propTypes = {
                text: PropTypes.string.isRequired,
                onClick: PropTypes.func.isRequired
            };

            // After
            interface ButtonProps {
                text: string;
                onClick: CallableFunction;
            }

            class Button extends React.Component<ButtonProps> {
                render() {
                    return <button onClick={this.props.onClick}>{this.props.text}</button>;
                }
            }
            ```
        """
        if self.parent_classes and len(self.parent_classes) > 0:
            react_parent = self.parent_classes[0]
            if "Component" in react_parent.source:
                if interface_name := self.convert_to_react_interface():
                    if isinstance(react_parent, GenericType):
                        react_parent.parameters.insert(0, interface_name)
                    else:
                        react_parent.insert_after(f"<{interface_name}>", newline=False)

    @writer
    def class_component_to_function_component(self) -> None:
        """Converts a class component to a function component."""
        return self.ctx.ts_declassify.declassify(self.source, filename=os.path.basename(self.file.file_path))
