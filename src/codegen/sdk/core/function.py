from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, Self, override

from typing_extensions import TypeVar

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.autocommit import reader, writer
from codegen.sdk.core.detached_symbols.code_block import CodeBlock
from codegen.sdk.core.detached_symbols.decorator import Decorator
from codegen.sdk.core.detached_symbols.parameter import Parameter
from codegen.sdk.core.expressions.type import Type
from codegen.sdk.core.interfaces.callable import Callable
from codegen.sdk.core.interfaces.chainable import Chainable
from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.core.interfaces.supports_generic import SupportsGenerics
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.enums import SymbolType
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.extensions.utils import cached_property
from codegen.shared.decorators.docs import apidoc, noapidoc
from codegen.visualizations.enums import VizNode

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.export import Export
    from codegen.sdk.core.file import File
    from codegen.sdk.core.import_resolution import Import, WildcardImport
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.statements.return_statement import ReturnStatement
    from codegen.sdk.core.symbol import Symbol


TDecorator = TypeVar("TDecorator", bound="Decorator", default=Decorator)
TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock", default=CodeBlock)
TParameter = TypeVar("TParameter", bound="Parameter", default=Parameter)
TType = TypeVar("TType", bound="Type", default=Type)


@apidoc
class Function(
    SupportsGenerics[TType],
    HasBlock[TCodeBlock, TDecorator],
    Callable[TParameter, TType],
    Chainable,
    Generic[TDecorator, TCodeBlock, TParameter, TType],
):
    """Abstract representation of a Function.

    Attributes:
        symbol_type: The type of symbol, set to SymbolType.Function.
    """

    symbol_type = SymbolType.Function

    @property
    @abstractmethod
    def is_private(self) -> bool:
        """Determines if a function has a private access modifier.

        A function is considered private if it starts with an underscore (_) in Python, or has a private keyword in other languages.

        Returns:
            bool: True if the function has a private access modifier, False otherwise.
        """

    @property
    @abstractmethod
    def is_magic(self) -> bool:
        """Returns True if function is a magic method.

        Determines if the function is a magic method based on Python's double underscore naming convention.
        A magic method in Python is a special method surrounded by double underscores (e.g., __init__, __str__).

        Returns:
            bool: True if the function is a magic method, False otherwise.
        """

    @property
    def is_overload(self) -> bool:
        """Indicates whether the function is an overloaded function in a multi-function definition.

        Determines if this function is part of a function overload group in the codebase. This property helps identify
        functions that have multiple implementations with different parameter types.

        Returns:
            bool: False, as this base implementation does not support overloads.
        """
        return False

    @property
    @abstractmethod
    def is_property(self) -> bool:
        """Returns whether this function is a property.

        Determines if the function has been decorated with `@property` decorator.

        Returns:
            bool: True if the function is a property, False otherwise.
        """
        pass

    @property
    def is_method(self) -> bool:
        """Returns whether the function is a method of a class.

        Determines if this function is defined within a class context. It checks if the parent of the function is a Class.

        Returns:
            bool: True if the function is a method within a class, False otherwise.
        """
        from codegen.sdk.core.class_definition import Class

        return isinstance(self.parent.parent.parent, Class)

    @property
    def is_constructor(self) -> bool:
        """Determines if the current function is a constructor method.

        A constructor method is a special method associated with a class. This property checks if the function
        is both a class method and has a name that matches the class's constructor keyword.

        Returns:
            bool: True if the function is a constructor method of a class, False otherwise.
        """
        return self.is_method and self.name == self.parent_class.constructor_keyword

    @property
    def is_async(self) -> bool:
        """Returns True if the function is asynchronous.

        A property that determines whether the function has been defined with the 'async' keyword.

        Returns:
            bool: True if the function is asynchronous, False otherwise.
        """
        return any("async" == x.type for x in self.ts_node.children)

    @noapidoc
    @reader
    def resolve_name(self, name: str, start_byte: int | None = None, strict: bool = True) -> Generator[Symbol | Import | WildcardImport]:
        from codegen.sdk.core.class_definition import Class

        for symbol in self.valid_symbol_names:
            if symbol.name == name and (start_byte is None or (symbol.start_byte if isinstance(symbol, Class | Function) else symbol.end_byte) <= start_byte):
                yield symbol
                return
        yield from super().resolve_name(name, start_byte, strict=strict)

    @cached_property
    @noapidoc
    def valid_symbol_names(self) -> list[Importable]:
        return sort_editables(self.parameters.symbols + self.descendant_symbols, reverse=True)

    # Faster implementation which uses more memory
    # @noapidoc
    # @reader
    # def resolve_name(self, name: str, start_byte: int | None = None) -> Symbol | Import | WildcardImport | None:
    #     if symbols := self.valid_symbol_names.get(name, None):
    #         for symbol in symbols:
    #             from codegen.sdk.core.class_definition import Class
    #
    #             if (symbol.start_byte if isinstance(symbol, Class | Function) else symbol.end_byte) <= start_byte:
    #                 return symbol
    #     return super().resolve_name(name, start_byte)
    #
    # @cached_property
    # @noapidoc
    # def valid_symbol_names(self) -> dict[str, list[Importable]]:
    #     ret = defaultdict(list)
    #     for elem in sort_editables(self.parameters.symbols + self.descendant_symbols, reverse=True):
    #         ret[elem.name].append(elem)
    #     return ret
    #
    ###########################################################################################################
    # PROPERTIES
    ###########################################################################################################

    @property
    @abstractmethod
    @reader
    def function_signature(self) -> str:
        """Returns the signature of the function as a string.

        A property that returns the complete function signature including its declaration, parameters, and return type annotation. The signature format
        varies based on the language, but follows the standard syntax for function declarations in that language.

        Returns:
            str: A string representation of the function's complete signature.
        """
        # TODO: rename to declaration_docstring?

    @property
    @reader
    def return_statements(self) -> list[ReturnStatement]:
        """Returns a list of all return statements within this function's body.

        Provides access to return statements in the function's code block, which is useful for analyzing return patterns,
        identifying early returns, and examining return types.

        Args:
            None

        Returns:
            list[ReturnStatement]: A list of all return statements found within the function's body.
        """
        return self.code_block.get_statements(statement_type=StatementType.RETURN_STATEMENT)

    @property
    @reader
    def nested_functions(self) -> list[Self]:
        """Returns a list of nested functions defined within this function's code block.

        Retrieves all functions that are defined within the current function's body. The functions are sorted by their position in the file.

        Returns:
            list[Self]: A list of Function objects representing nested functions within this function's body, sorted by position in the file.
        """
        functions = [m.symbol for m in self.code_block.symbol_statements if isinstance(m.symbol, self.__class__)]
        return functions

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def set_return_type(self, new_return_type: str) -> None:
        """Sets the return type annotation for the function.

        Sets or updates the return type annotation of the function. If an empty string is provided,
        the return type annotation will be removed.

        Args:
            new_return_type (str): The new return type annotation to be set. Use an empty string to remove
                the return type annotation.

        Returns:
            None
        """
        # TODO: other set APIs should be consistent and also offer a remove option
        # TODO: if new_return_type is empty string, should remove the return type
        self.return_type.edit(new_return_type)

    @writer
    def asyncify(self) -> None:
        """Modifies the function to be asynchronous.

        Converts a synchronous function to be asynchronous by adding the 'async' keyword to its definition if it is not already
        marked as asynchronous.

        Returns:
            None

        Note:
            This method has no effect if the function is already asynchronous.
        """
        if self.is_async:
            return

        self.add_keyword("async")

    @writer
    def rename_local_variable(self, old_var_name: str, new_var_name: str, fuzzy_match: bool = False) -> None:
        """Renames a local variable and all its usages within a function body.

        The method searches for matches of the old variable name within the function's code block and replaces them with the new variable name. It excludes parameter names from being renamed.

        Args:
            old_var_name (str): The current name of the local variable to be renamed.
            new_var_name (str): The new name to give to the local variable.
            fuzzy_match (bool, optional): If True, matches variable names that contain old_var_name. Defaults to False.

        Returns:
            None: The method modifies the AST in place.
        """
        matches = self.code_block.get_assignments(old_var_name, fuzzy=fuzzy_match, parameters=False)
        for match in matches:
            new_name = new_var_name
            if fuzzy_match:
                new_name = match.name.replace(old_var_name, new_var_name)
            match.rename(new_name)

    @writer
    def insert_statements(self, lines: str, index: int = 0) -> None:
        """Inserts lines of code into the function body at the specified index.

        Adds the provided lines as statements within the function's body at the given position. If index is 0, the lines will be prepended at the start of the function body.

        Args:
            lines (str): The code lines to insert into the function body.
            index (int, optional): The position in the function body where the lines should be inserted. Defaults to 0.

        Returns:
            None

        Raises:
            ValueError: If the provided index is out of range for the function's statements.
        """
        if index == 0:
            return self.prepend_statements(lines)

        statements = self.code_block.statements
        if index >= len(statements):
            msg = f"Index {index} out of range for function {self.name}"
            raise ValueError(msg)

        first_statement = self.code_block.statements[index]
        first_statement.insert_before(lines)

    @writer
    def prepend_statements(self, lines: str) -> None:
        """Prepends the provided code to the beginning of the function body.

        Args:
            lines (str): The code to be prepended to the function body.

        Returns:
            None

        Note:
            This method handles indentation automatically to maintain proper code formatting.
        """
        self.code_block.statements[0].insert_before(lines, fix_indentation=True)

    @writer
    def add_statements(self, lines: str) -> None:
        """Adds statements to the end of a function body.

        Adds the provided lines of code to the end of the function's code block. The method handles proper indentation automatically.

        Args:
            lines (str): The lines of code to be added at the end of the function body.

        Returns:
            None
        """
        last_statement = self.code_block.statements[-1]
        last_statement.insert_after(lines, fix_indentation=True)

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        if self.is_method and self.is_property:
            if ret := self.return_type:
                yield from self.with_resolution_frame(ret, direct=False)
        else:
            yield ResolutionStack(self)

    @property
    @noapidoc
    def viz(self) -> VizNode:
        return VizNode(file_path=self.filepath, start_point=self.start_point, end_point=self.end_point, name=self.name, symbol_name=self.__class__.__name__)

    @property
    @noapidoc
    def parent_symbol(self) -> Symbol | File | Import | Export:
        """Searches up its parent stack until it finds a top level symbol."""
        if self.is_method:
            if self.parent_class.is_top_level:
                return self
        return super().parent_symbol

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Gets all function calls within the function and its parameters.

        Retrieves all function calls that appear within this function's body and within its parameter
        declarations, sorted by position in the file.

        Args:
            None

        Returns:
            list[FunctionCall]: A sorted list of all function calls within the function and its parameters.
            Function calls may appear multiple times in the list.
        """
        fcalls = super().function_calls
        for p in self.parameters:
            fcalls.extend(p.function_calls)
        return sort_editables(fcalls, dedupe=False)

    ####################################################################################################################
    # EXTERNAL APIS
    ####################################################################################################################

    @property
    @reader
    def inferred_return_type(self) -> str | None:
        """Gets the inferred type of the function from the language's native language engine / compiler.

        Only enabled for specific languages that support native type inference.
        """
        if self.ctx.language_engine:
            return self.ctx.language_engine.get_return_type(self)
        else:
            msg = "Language engine not enabled for this repo or language."
            raise NotImplementedError(msg)

    @property
    @noapidoc
    def descendant_symbols(self) -> Sequence[Importable]:
        symbols = [self]
        for param in self.parameters:
            symbols.extend(param.descendant_symbols)
        if self.return_type:
            symbols.extend(self.return_type.descendant_symbols)
        symbols.extend(self.code_block.descendant_symbols)
        return symbols

    @noapidoc
    def register_api(self, url: str):
        self.ctx.global_context.multigraph.api_definitions[url] = self
