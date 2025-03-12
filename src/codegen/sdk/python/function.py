from __future__ import annotations

import re
from typing import TYPE_CHECKING, override

from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.function import Function
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.extensions.utils import cached_property
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.detached_symbols.decorator import PyDecorator
from codegen.sdk.python.detached_symbols.parameter import PyParameter
from codegen.sdk.python.expressions.type import PyType
from codegen.sdk.python.interfaces.has_block import PyHasBlock
from codegen.sdk.python.placeholder.placeholder_return_type import PyReturnTypePlaceholder
from codegen.sdk.python.symbol import PySymbol
from codegen.shared.decorators.docs import noapidoc, py_apidoc
from codegen.shared.logging.get_logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.import_resolution import Import, WildcardImport
    from codegen.sdk.core.interfaces.has_name import HasName
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.symbol import Symbol

logger = get_logger(__name__)


@py_apidoc
class PyFunction(Function[PyDecorator, PyCodeBlock, PyParameter, PyType], PyHasBlock, PySymbol):
    """Extends Function for Python codebases."""

    _decorated_node: TSNode | None

    def __init__(self, ts_node: TSNode, file_id: NodeId, ctx: CodebaseContext, parent: PyHasBlock, decorated_node: TSNode | None = None) -> None:
        super().__init__(ts_node, file_id, ctx, parent)
        self._decorated_node = decorated_node

    @cached_property
    @reader
    def is_private(self) -> bool:
        """Determines if a method is a private method.

        Private methods in Python start with an underscore and are not magic methods.

        Returns:
            bool: True if the method is private (starts with '_' and is not a magic method), False otherwise.
        """
        return self.name.startswith("_") and not self.is_magic

    @cached_property
    @reader
    def is_magic(self) -> bool:
        """Determines if a method is a magic method.

        A magic method in Python is a method that starts and ends with double underscores, such as `__init__` or `__str__`.
        This property checks if the current method's name matches this pattern.

        Returns:
            bool: True if the method is a magic method (name starts and ends with double underscores), False otherwise.
        """
        return self.name.startswith("__") and self.name.endswith("__")

    @property
    @reader
    def is_overload(self) -> bool:
        """Determines whether a function is decorated with an overload decorator.

        Checks if the function has any of the following decorators:
        - @overload
        - @typing.overload
        - @typing_extensions.overload

        Returns:
            bool: True if function has an overload decorator, False otherwise.
        """
        return any(dec in ("@overload", "@typing.overload", "@typing_extensions.overload") for dec in self.decorators)

    @property
    @reader
    def is_property(self) -> bool:
        """Determines if the function is a property.

        Checks the decorators list to see if the function has a `@property` or `@cached_property` decorator.

        Returns:
            bool: True if the function has a `@property` or `@cached_property` decorator, False otherwise.
        """
        return any(dec in ("@property", "@cached_property") for dec in self.decorators)

    @property
    @reader
    def is_static_method(self) -> bool:
        """Determines if the function is a static method.

        Checks the function's decorators to determine if it is decorated with the @staticmethod decorator.

        Returns:
            bool: True if the function is decorated with @staticmethod, False otherwise.
        """
        return "@staticmethod" in self.decorators

    @property
    @reader
    def is_class_method(self) -> bool:
        """Indicates whether the current function is decorated with @classmethod.

        Args:
            self: The PyFunction instance.

        Returns:
            bool: True if the function is decorated with @classmethod, False otherwise.
        """
        return "@staticmethod" in self.decorators

    @noapidoc
    @reader
    def resolve_name(self, name: str, start_byte: int | None = None, strict: bool = True) -> Generator[Symbol | Import | WildcardImport]:
        if self.is_method:
            if not self.is_static_method:
                if len(self.parameters.symbols) > 0:
                    if name == self.parameters[0].name:
                        yield self.parent_class
                        return
                if name == "super()":
                    yield self.parent_class
                    return
        yield from super().resolve_name(name, start_byte, strict=strict)

    @noapidoc
    @commiter
    def parse(self, ctx: CodebaseContext) -> None:
        super().parse(ctx)
        self.return_type = self.child_by_field_name("return_type", placeholder=PyReturnTypePlaceholder)
        if parameters_node := self.ts_node.child_by_field_name("parameters"):
            params = [
                x
                for x in parameters_node.children
                if x.type
                in (
                    "identifier",
                    "typed_parameter",
                    "default_parameter",
                    "typed_default_parameter",
                    "list_splat_pattern",
                    "dictionary_splat_pattern",
                )
            ]
            self._parameters = Collection(parameters_node, self.file_node_id, self.ctx, self)
            self._parameters._init_children([PyParameter(x, i, self._parameters) for (i, x) in enumerate(params)])
        else:
            logger.warning(f"Couldn't find parameters for {self!r}")
            self._parameters = []
        self.type_parameters = self.child_by_field_name("type_parameters")

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        dest = dest or self.self_dest

        # =====[ Decorated functions ]=====
        for decorator in self.decorators:
            decorator._compute_dependencies(usage_type, dest)

        # =====[ Identifiers in Body ]=====
        self.code_block._compute_dependencies(usage_type, dest)
        if self.type_parameters:
            self.type_parameters._compute_dependencies(UsageKind.GENERIC, dest)
        # =====[ Return type ]=====
        if self.return_type:
            # Need to parse all the different types
            self.return_type._compute_dependencies(UsageKind.RETURN_TYPE, dest)

    @property
    @reader
    def function_signature(self) -> str:
        """Returns the function signature as a string.

        Gets the string representation of the function's signature, including name, parameters, and return type.

        Args:
            None

        Returns:
            str: A string containing the complete function signature including the function name,
                parameters (if any), return type annotation (if present), and a colon.
        """
        func_def_src = f"def {self.name}"
        if self.parameters is not None:
            func_def_src += self.parameters.source
        if self.return_type:
            func_def_src += " -> " + self.return_type.source
        func_def_src += ":"
        return func_def_src

    @property
    @reader
    def body(self) -> str:
        """Returns the body of the function as a string.

        Gets the source code of the function's body, excluding the docstring if present.

        Returns:
            str: The function's body content as a string, with any docstring removed and whitespace stripped.
        """
        text = self.code_block.source
        if self.docstring is not None:
            return text.replace(self.docstring.extended_source, "").strip()
        return text

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def prepend_statements(self, lines: str) -> None:
        """Prepends statements to the start of the function body.

        Given a string of code statements, adds them at the beginning of the function body, right after any existing docstring. The method handles indentation automatically.

        Args:
            lines (str): The code statements to prepend to the function body.

        Returns:
            None: This method modifies the function in place.
        """
        statements = self.code_block.statements
        first_statement = statements[0] if self.docstring is None else statements[1]
        first_statement.insert_before(lines, fix_indentation=True)

    @writer
    @override
    def set_return_type(self, new_return_type: str) -> None:
        """Sets or modifies the return type annotation of a function.

        Updates the function's return type annotation by either modifying an existing return type or adding a new one.
        If an empty string is provided as the new return type, removes the existing return type annotation.

        Args:
            new_return_type (str): The new return type annotation to set. Provide an empty string to remove the return type annotation.

        Returns:
            None
        """
        # Clean any leading -> from new_return_type
        new_return_type = new_return_type.removeprefix(" -> ")

        if self.return_type:
            # Case: return type node DOES exist, and new_return_type is not empty, replace return type
            if new_return_type:
                self.return_type.edit(new_return_type)
            # Case: return type node DOES exist, and new_return_type is empty, remove return type
            else:
                # TODO: instead use prev sibling to find where the -> is?
                new_source = re.sub(r" -> .+:", ":", self.source, 1)
                self.edit(new_source)
        else:
            # Case: return type node DOES NOT exist
            self.return_type.edit(new_return_type)
