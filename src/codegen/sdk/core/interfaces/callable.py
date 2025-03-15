from dataclasses import dataclass
from typing import TYPE_CHECKING, Generic, Self, TypeVar

from codegen.sdk.core.autocommit import reader
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.sdk.core.interfaces.usable import Usable
from codegen.sdk.core.placeholder.placeholder import Placeholder
from codegen.sdk.core.symbol_group import SymbolGroup
from codegen.shared.decorators.docs import apidoc

if TYPE_CHECKING:
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.detached_symbols.parameter import Parameter
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.external_module import ExternalModule
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.symbol import Symbol


@dataclass
class FunctionCallDefinition:
    """Represents a function call and its definitions.

    This class encapsulates information about a function call and the possible
    callable entities that define it.

    Attributes:
        call (FunctionCall): The function call object representing the invocation.
        callables (List[Union[Function, Class, ExternalModule]]): A list of callable
            entities that define the function being called.
    """

    call: FunctionCall
    callables: list["Function | Class | ExternalModule"]


TParameter = TypeVar("TParameter", bound="Parameter")
TType = TypeVar("TType", bound="Type")


@apidoc
class Callable(Usable, Generic[TParameter, TType]):
    """Any symbol that can be invoked with arguments eg.

    Function, Class, Decorator, ExternalModule

    Attributes:
        return_type: The type of value returned by the callable, or a placeholder.
    """

    _parameters: SymbolGroup[TParameter, Self] | list[TParameter]

    return_type: TType | Placeholder[Self]

    @property
    @reader(cache=False)
    def call_sites(self) -> list[FunctionCall]:
        """Returns all call sites (invocations) of this callable in the codebase.

        Finds all locations in the codebase where this callable is invoked/called. Call sites exclude imports, certain exports, and external references.

        Returns:
            list[FunctionCall]: A list of FunctionCall objects representing each invocation of this callable.
            Returns empty list if the callable has no name.
        """
        # TODO - rename this and `function_calls` to be more clear
        call_sites: list[FunctionCall] = []

        for usage in self.usages:
            if isinstance(usage.match, FunctionCall):
                call_sites.append(usage.match)

        return list(dict.fromkeys(call_sites))

    @property
    @reader
    def parameters(self) -> SymbolGroup[TParameter, Self] | list[TParameter]:
        """Retrieves all parameters of a callable symbol.

        This property provides access to all parameters of a callable symbol (function, class, decorator, or external module).
        Parameters are stored as a SymbolGroup containing Parameter objects.

        Returns:
            SymbolGroup[TParameter, Self] | list[TParameter]: A group of Parameter objects representing the callable's parameters,
            or an empty list if the callable has no parameters.
        """
        return self._parameters

    @reader
    def get_parameter(self, name: str, optional: bool = False) -> TParameter | None:
        """Gets a specific parameter from the callable's parameters list by name.

        Args:
            name (str): The name of the parameter to retrieve.
            optional (bool, optional): If True, returns None instead of raising an error if the parameter is not found.

        Returns:
            TParameter | None: The parameter with the specified name, or None if no parameter with that name exists or if there are no parameters.
        """
        parameter = [x for x in self._parameters if x.name == name]
        if not parameter:
            if not optional:
                msg = f"Parameter {name} not found in callable {self.name}. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(parameter) > 1:
            msg = f"Multiple parameters with name {name} found in callable {self.name}. Use get_parameter_by_type to resolve."
            raise ValueError(msg)
        return parameter[0]

    @reader
    def get_parameter_by_index(self, index: int, optional: bool = False) -> TParameter | None:
        """Returns the parameter at the given index.

        Retrieves a parameter from the callable's parameter list based on its positional index.

        Args:
            index (int): The index of the parameter to retrieve.
            optional (bool, optional): If True, returns None instead of raising an error if the parameter is not found.

        Returns:
            TParameter | None: The parameter at the specified index, or None if the parameter list
                is empty or the index does not exist.
        """
        parameter = [x for x in self._parameters if x.index == index]
        if not parameter:
            if not optional:
                msg = f"Parameter at index {index} not found in callable {self.name}. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(parameter) > 1:
            msg = f"Multiple parameters at index {index} found in callable {self.name}. Use get_parameter_by_type to resolve."
            raise ValueError(msg)
        return parameter[0]

    @reader
    def get_parameter_by_type(self, type: "Symbol", optional: bool = False) -> TParameter | None:
        """Retrieves a parameter from the callable by its type.

        Searches through the callable's parameters to find a parameter with the specified type.

        Args:
            type (Symbol): The type to search for.
            optional (bool, optional): If True, returns None instead of raising an error if the parameter is not found.

        Returns:
            TParameter | None: The parameter with the specified type, or None if no parameter is found or if the callable has no parameters.
        """
        if self._parameters is None:
            return None
        parameter = [x for x in self._parameters if x.type == type]
        if not parameter:
            if not optional:
                msg = f"Parameter of type {type} not found in callable {self.name}. Use optional=True to return None instead."
                raise ValueError(msg)
            return None
        if len(parameter) > 1:
            msg = f"Multiple parameters of type {type} found in callable {self.name}. Use get_parameter_by_name to resolve."
            raise ValueError(msg)
        return parameter[0]
