from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING

from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.typescript.detached_symbols.decorator import TSDecorator
from codegen.sdk.typescript.detached_symbols.parameter import TSParameter
from codegen.sdk.typescript.enums import TSFunctionTypeNames
from codegen.sdk.typescript.expressions.type import TSType
from codegen.sdk.typescript.interfaces.has_block import TSHasBlock
from codegen.sdk.typescript.placeholder.placeholder_return_type import TSReturnTypePlaceholder
from codegen.sdk.typescript.symbol import TSSymbol
from codegen.sdk.utils import find_all_descendants
from codegen.shared.decorators.docs import noapidoc, ts_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.import_resolution import Import, WildcardImport
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.export_statement import ExportStatement
    from codegen.sdk.core.statements.symbol_statement import SymbolStatement
    from codegen.sdk.core.symbol import Symbol
    from codegen.sdk.typescript.detached_symbols.code_block import TSCodeBlock
    from codegen.sdk.typescript.detached_symbols.promise_chain import TSPromiseChain
_VALID_TYPE_NAMES = {function_type.value for function_type in TSFunctionTypeNames}
logger = get_logger(__name__)


@ts_apidoc
class TSFunction(Function[TSDecorator, "TSCodeBlock", TSParameter, TSType], TSHasBlock, TSSymbol):
    """Representation of a Function in JavaScript/TypeScript"""

    @noapidoc
    @commiter
    def parse(self, ctx: CodebaseContext) -> None:
        super().parse(ctx)

        self.return_type = self.child_by_field_name("return_type", placeholder=TSReturnTypePlaceholder)
        if parameters_node := self.ts_node.child_by_field_name("parameters"):
            self._parameters = Collection(parameters_node, self.file_node_id, self.ctx, self)
            params = [x for x in parameters_node.children if x.type in ("required_parameter", "optional_parameter")]
            symbols = None
            # Deconstructed object parameters
            if len(params) == 1:
                pattern = params[0].child_by_field_name("pattern")
                type_annotation = None
                if type_node := params[0].child_by_field_name("type"):
                    type_annotation = self._parse_type(type_node)
                if pattern and pattern.type == "object_pattern":
                    params = [x for x in pattern.children if x.type in ("shorthand_property_identifier_pattern", "object_assignment_pattern", "pair_pattern")]
                    symbols = [TSParameter(x, i, self._parameters, type_annotation) for (i, x) in enumerate(params)]
            # Default case - regular parameters
            if symbols is None:
                symbols = [TSParameter(x, i, self._parameters) for (i, x) in enumerate(params)]
            self._parameters._init_children(symbols)
        elif parameters_node := self.ts_node.child_by_field_name("parameter"):
            self._parameters = Collection(parameters_node, self.file_node_id, self.ctx, self)
            self._parameters._init_children([TSParameter(parameters_node, 0, self._parameters)])
        else:
            logger.warning(f"Couldn't find parameters for {self!r}")
            self._parameters = []
        self.type_parameters = self.child_by_field_name("type_parameters")

    @property
    @reader
    def function_type(self) -> TSFunctionTypeNames:
        """Gets the type of function from its TreeSitter node.

        Extracts and returns the type of function (e.g., arrow function, generator function, function expression)
        from the node's type information.

        Args:
            None: Property method that uses instance's ts_node.

        Returns:
            TSFunctionTypeNames: The function type enum value representing the specific type of function.
        """
        return TSFunctionTypeNames(self.ts_node.type)

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        # If a destination is provided, use it, otherwise use the default destination
        # This is used for cases where a non-symbol (eg. argument) value parses as a function
        dest = dest or self.self_dest

        # =====[ Typed Parameters ]=====
        # Have to grab types from the parameters
        if self.parameters is not None:
            for param in self.parameters:
                assignment_patterns = find_all_descendants(param.ts_node, {"object_pattern", "object_assignment_pattern", "assignment_pattern"})
                if assignment_patterns:
                    dest.add_all_identifier_usages_for_child_node(UsageKind.GENERIC, assignment_patterns[0])
        if self.type_parameters:
            self.type_parameters._compute_dependencies(UsageKind.GENERIC, dest)
        # =====[ Return type ]=====
        if self.return_type:
            # Need to parse all the different types
            self.return_type._compute_dependencies(UsageKind.RETURN_TYPE, dest)

        # =====[ Code Block ]=====
        self.code_block._compute_dependencies(usage_type, dest)

    @classmethod
    @noapidoc
    def from_function_type(cls, ts_node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: SymbolStatement | ExportStatement) -> TSFunction:
        """Creates a TSFunction object from a function declaration."""
        if ts_node.type not in [function_type.value for function_type in TSFunctionTypeNames]:
            msg = f"Node type={ts_node.type} is not a function declaration"
            raise ValueError(msg)
        file = ctx.get_node(file_node_id)
        if canonical := file._range_index.get_canonical_for_range(ts_node.range, ts_node.kind_id):
            return canonical
        return cls(ts_node, file_node_id, ctx, parent=parent)

    @staticmethod
    @noapidoc
    def _get_name_node(ts_node: TSNode) -> TSNode | None:
        if ts_node.type == "function_declaration":
            return ts_node.child_by_field_name("name")
        elif ts_node.type == "function_expression":
            if name := ts_node.child_by_field_name("name"):
                return name
            return ts_node.parent.child_by_field_name("name")
        elif ts_node.type == "arrow_function":
            ts_node = ts_node.parent
            while ts_node.type in ("parenthesized_expression", "binary_expression"):
                ts_node = ts_node.parent
            if ts_node.type == "pair":
                return ts_node.child_by_field_name("key")
            elif ts_node.type == "return_statement":
                func_expression = next((x for x in ts_node.children if x.type == ("function_expression")), None)
                if func_expression:
                    return func_expression.child_by_field_name("name")
        return ts_node.child_by_field_name("name")

    @property
    @reader
    def function_signature(self) -> str:
        """Returns a string representation of the function's signature.

        Generates a string containing the full function signature including name, parameters, and return type
        based on the function's type (arrow function, generator function, function expression, etc.).

        Returns:
            str: A string containing the complete function signature. For example: 'function foo(bar: string): number'

        Raises:
            NotImplementedError: If the function type is not implemented.
        """
        if self.function_type == TSFunctionTypeNames.FunctionDeclaration:
            func_def_src = f"function {self.name}"
        elif self.function_type == TSFunctionTypeNames.GeneratorFunctionDeclaration:
            func_def_src = f"function* {self.name}"
        elif self.function_type == TSFunctionTypeNames.ArrowFunction:
            func_def_src = f"{self.name} = "
        elif self.function_type == TSFunctionTypeNames.FunctionExpression:
            func_def_src = f"{self.name} = function"
        else:
            msg = "function type not implemented"
            raise NotImplementedError(msg)
        if self.parameters is not None:
            func_def_src += self.parameters.source
        if self.return_type:
            func_def_src += ": " + self.return_type.source
        return func_def_src

    @cached_property
    @reader
    def is_private(self) -> bool:
        """Determines if a function is private based on its accessibility modifier.

        This property examines the function's accessibility modifier to determine if it's marked as private. In TypeScript, this means the function has the 'private' keyword.

        Returns:
            bool: True if the function has a 'private' accessibility modifier, False otherwise.
        """
        modifier = self.ts_node.children[0]
        return modifier.type == "accessibility_modifier" and modifier.text == b"private"

    @cached_property
    @reader
    def is_magic(self) -> bool:
        """Returns whether this method is a magic method.

        A magic method is a method whose name starts and ends with double underscores, like __init__ or __str__.
        In this implementation, all methods are considered non-magic in TypeScript.

        Returns:
            bool: False, as TypeScript does not have magic methods.
        """
        return False

    @property
    @reader
    def is_anonymous(self) -> bool:
        """Property indicating whether a function is anonymous.

        Returns True if the function has no name or if its name is an empty string.

        Returns:
            bool: True if the function is anonymous, False otherwise.
        """
        return not self.name or self.name.strip() == ""

    @property
    def is_async(self) -> bool:
        """Determines if the function is asynchronous.

        Checks the function's node children to determine if the function is marked as asynchronous.

        Returns:
            bool: True if the function is asynchronous (has 'async' keyword), False otherwise.
        """
        return any("async" == x.type for x in self.ts_node.children)

    @property
    @reader
    def is_arrow(self) -> bool:
        """Returns True iff the function is an arrow function.

        Identifies whether the current function is an arrow function (lambda function) in TypeScript/JavaScript.

        Returns:
            bool: True if the function is an arrow function, False otherwise.
        """
        return self.function_type == TSFunctionTypeNames.ArrowFunction

    @property
    @reader
    def is_property(self) -> bool:
        """Determines if the function is a property.

        Checks if any of the function's decorators are '@property' or '@cached_property'.

        Returns:
            bool: True if the function has a @property or @cached_property decorator, False otherwise.
        """
        return any(dec in ("@property", "@cached_property") for dec in self.decorators)

    @property
    @reader
    def _named_arrow_function(self) -> TSNode | None:
        """Returns the name of the named arrow function, if it exists."""
        if self.is_arrow:
            node = self.ts_node
            if name := self.get_name():
                node = name.ts_node
            parent = node.parent
            if parent.type == "variable_declarator":
                return parent.parent
        return None

    @property
    @reader
    def is_jsx(self) -> bool:
        """Determines if the function is a React component by checking if it returns a JSX element.

        A function is considered a React component if it contains at least one JSX element in its body
        and either has no name or has a name that starts with an uppercase letter.

        Returns:
            bool: True if the function is a React component, False otherwise.
        """
        # Must contain a React component
        if len(self.jsx_elements) == 0:
            return False
        # Must be uppercase name
        if not self.name:
            return True
        return self.name[0].isupper()

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def asyncify(self) -> None:
        """Modifies the function to be asynchronous, if it is not already.

        This method converts a synchronous function to be asynchronous by adding the 'async' keyword and wrapping
        the return type in a Promise if a return type exists.

        Returns:
            None

        Note:
            If the function is already asynchronous, this method does nothing.
        """
        if self.is_async:
            return
        self.add_keyword("async")
        if self.return_type and self.return_type.name != "Promise":
            self.return_type.insert_before("Promise<", newline=False)
            self.return_type.insert_after(">", newline=False)

    @writer
    def arrow_to_named(self, name: str | None = None) -> None:
        """Converts an arrow function to a named function in TypeScript/JavaScript.

        Transforms an arrow function into a named function declaration, preserving type parameters, parameters,
        return types, and function body. If the function is already asynchronous, the async modifier is preserved.

        Args:
            name (str | None): The name for the converted function. If None, uses the name of the variable
                the arrow function is assigned to.

        Returns:
            None

        Raises:
            ValueError: If name is None and the arrow function is not assigned to a named variable.
        """
        if not self.is_arrow or self.name is None:
            return

        if name is None and self._name_node is None:
            msg = "The `name` argument must be provided when converting an arrow function that is not assigned to any variable."
            raise ValueError(msg)

        node = self._named_arrow_function
        # Replace variable declaration with function declaration
        async_prefix = "async " if self.is_async else ""
        edit_start = node.start_byte
        type_param_node = self.ts_node.child_by_field_name("type_parameters")
        if param_node := self.ts_node.child_by_field_name("parameters"):
            edit_end = param_node.start_byte
            self._edit_byte_range(f"{async_prefix}function {name or self.name}{type_param_node.text.decode('utf-8') if type_param_node else ''}", edit_start, edit_end)
        elif param_node := self.ts_node.child_by_field_name("parameter"):
            edit_end = param_node.start_byte
            self._edit_byte_range(f"{async_prefix}function {name or self.name}{type_param_node.text.decode('utf-8') if type_param_node else ''}(", edit_start, edit_end)
            self.insert_at(param_node.end_byte, ")")

        # Remove the arrow =>
        if self.return_type:
            remove_start = self.return_type.end_byte + 1
        else:
            remove_start = param_node.end_byte + 1
        self.remove_byte_range(remove_start, self.code_block.start_byte)

        # Add brackets surrounding the code block if not already present
        if not self.code_block.source.startswith("{"):
            self.insert_at(self.code_block.start_byte, "{ return ")
            self.insert_at(node.end_byte, " }")

        # Move over variable type annotations as parameter type annotations
        if (type_node := node.named_children[0].child_by_field_name("type")) and len(param_node.named_children) == 1:
            destructured_param = self.parameters.ts_node.named_children[0]
            self.insert_at(destructured_param.end_byte, type_node.text.decode("utf-8"))

    @noapidoc
    @reader
    def resolve_name(self, name: str, start_byte: int | None = None, strict: bool = True) -> Generator[Symbol | Import | WildcardImport]:
        """Resolves the name of a symbol in the function.

        This method resolves the name of a symbol in the function. If the name is "this", it returns the parent class.
        Otherwise, it calls the superclass method to resolve the name.

        Args:
            name (str): The name of the symbol to resolve.
            start_byte (int | None): The start byte of the symbol to resolve.
            strict (bool): If True considers candidates that don't satisfy start byte if none do.

        Returns:
            Symbol | Import | WildcardImport: The resolved symbol, import, or wildcard import, or None if not found.
        """
        if self.is_method:
            if name == "this":
                yield self.parent_class
                return
        yield from super().resolve_name(name, start_byte, strict=strict)

    @staticmethod
    def is_valid_node(node: TSNode) -> bool:
        """Determines if a given tree-sitter node corresponds to a valid function type.

        This method checks if a tree-sitter node's type matches one of the valid function types defined in the _VALID_TYPE_NAMES set.

        Args:
            node (TSNode): The tree-sitter node to validate.

        Returns:
            bool: True if the node's type is a valid function type, False otherwise.
        """
        return node.type in _VALID_TYPE_NAMES

    @writer
    def convert_props_to_interface(self) -> None:
        """Converts React component props to TypeScript interfaces.

        For React components, converts inline props type definitions and PropTypes declarations
        to a separate interface. The interface will be named {ComponentName}Props and inserted
        before the component.

        Handles both simple types and complex types including:
        - Inline object type definitions
        - PropTypes declarations
        - Union types and optional props
        - Destructured parameters
        - Generic type parameters

        Example:
            ```typescript
            // Before
            function Button({ text, onClick }: { text: string, onClick: () => void }) {
                return <button onClick={onClick}>{text}</button>;
            }

            // After
            interface ButtonProps {
                text: string;
                onClick: () => void;
            }
            function Button({ text, onClick }: ButtonProps) {
                return <button onClick={onClick}>{text}</button>;
            }
            ```
        """
        if self.parameters and len(self.parameters) > 0:
            if interface_name := self.convert_to_react_interface():
                if not self.parameters[0].is_destructured:
                    self.parameters[0].edit(interface_name)
                else:
                    self.insert_at(self.parameters.ts_node.end_byte - 1, f": {interface_name}")

    @property
    @reader
    def promise_chains(self) -> list[TSPromiseChain]:
        """Returns a list of promise chains in the function.

        Returns:
            list[TSPromiseChain]: A list of promise chains in the function.
        """
        promise_chains = []
        visited_base_functions = set()
        function_calls = self.function_calls

        for function_call in function_calls:
            if function_call.name == "then" and function_call.base not in visited_base_functions:
                promise_chains.append(function_call.promise_chain)
                visited_base_functions.add(function_call.base)

        return promise_chains
