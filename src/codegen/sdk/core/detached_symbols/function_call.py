from __future__ import annotations

from typing import TYPE_CHECKING, Generic, Self, TypeVar, override

from codegen.sdk.codebase.resolution_stack import ResolutionStack
from codegen.sdk.core.autocommit import reader, remover, writer
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.detached_symbols.argument import Argument
from codegen.sdk.core.expressions import Expression, Name, Value
from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
from codegen.sdk.core.expressions.generic_type import GenericType
from codegen.sdk.core.expressions.unpack import Unpack
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.interfaces.resolvable import Resolvable
from codegen.sdk.core.symbol_groups.collection import Collection
from codegen.sdk.enums import NodeType
from codegen.sdk.extensions.sort import sort_editables
from codegen.sdk.extensions.utils import cached_property, is_descendant_of
from codegen.sdk.typescript.detached_symbols.promise_chain import TSPromiseChain
from codegen.sdk.typescript.enums import TSFunctionTypeNames
from codegen.sdk.utils import find_first_ancestor
from codegen.shared.decorators.docs import apidoc, noapidoc
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from collections.abc import Generator

    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.detached_symbols.parameter import Parameter
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.interfaces.callable import Callable
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.interfaces.importable import Importable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.visualizations.enums import VizNode

Parent = TypeVar("Parent", bound="Expression | None")


@apidoc
class FunctionCall(Expression[Parent], HasName, Resolvable, Generic[Parent]):
    """Abstract representation of a function invocation, e.g. in Python:
    ```
    def f():
        g()  # FunctionCall
    ```
    """

    _arg_list: Collection[Argument, Self]

    def __init__(self, node: TSNode, file_node_id: NodeId, ctx: CodebaseContext, parent: Parent) -> None:
        super().__init__(node, file_node_id, ctx, parent)
        # =====[ Grab the function name ]=====
        self._name_node = self.child_by_field_name("function", default=Name) or self.child_by_field_name("constructor", default=Name)
        if self._name_node is not None and self._name_node.ts_node.type in ("unary_expression", "await_expression"):
            self._name_node = self._parse_expression(self._name_node.ts_node.children[-1], default=Name)
        # =====[ Grab the arg list ]=====
        arg_list_node = node.child_by_field_name("arguments")
        if arg_list_node is None:
            msg = f"Failed to parse function call. Child 'argument_list' node does not exist. Source: {self.source}"
            raise ValueError(msg)
        args = [Argument(x, i, self) for i, x in enumerate(arg_list_node.named_children) if x.type != "comment"]
        self._arg_list = Collection(arg_list_node, self.file_node_id, self.ctx, self, children=args)

    def __repr__(self) -> str:
        """Custom string representation showing the function call chain structure.

        Format: FunctionCall(name=current, pred=pred_name, succ=succ_name, base=base_name)

        It will only print out predecessor, successor, and base that are of type FunctionCall. If it's a property, it will not be logged
        """
        # Helper to safely get name

        # Get names for each part
        parts = [f"name='{self.name}'"]

        if self.predecessor and isinstance(self.predecessor, FunctionCall):
            parts.append(f"predecessor=FunctionCall(name='{self.predecessor.name}')")

        if self.successor and isinstance(self.successor, FunctionCall):
            parts.append(f"successor=FunctionCall(name='{self.successor.name}')")

        parts.append(f"filepath='{self.file.filepath}'")

        return f"FunctionCall({', '.join(parts)})"

    @classmethod
    def from_usage(cls, node: Editable[Parent], parent: Parent | None = None) -> Self | None:
        """Creates a FunctionCall object from an Editable instance that represents a function call.

        Takes an Editable node that potentially represents a function call and creates a FunctionCall object from it.
        Useful when working with search results from the Editable API that may contain function calls.

        Args:
            node (Editable[Parent]): The Editable node that potentially represents a function call.
            parent (Parent | None): The parent node for the new FunctionCall. If None, uses the parent from the input node.

        Returns:
            Self | None: A new FunctionCall object if the input node represents a function call, None otherwise.
        """
        call_node = find_first_ancestor(node.ts_node, ["call", "call_expression"])
        if call_node is None:
            return None
        return cls(call_node, node.file_node_id, node.ctx, parent or node.parent)

    @property
    @reader
    def parent_function(self) -> Function | None:
        """Retrieves the parent function of the current function call.

        Returns the Function object that contains this function call, useful for understanding the context in which a function call is made.

        Returns:
            Function | None: The parent Function object containing this function call, or None if not found or if the function call is not within a function.
        """
        # HACK: This is temporary until we establish a full parent path
        if self.file.programming_language == ProgrammingLanguage.TYPESCRIPT:
            if func := find_first_ancestor(self.ts_node, [function_type.value for function_type in TSFunctionTypeNames]):
                from codegen.sdk.typescript.function import TSFunction

                return TSFunction.from_function_type(func, self.file_node_id, self.ctx, self.parent)
        elif self.file.programming_language == ProgrammingLanguage.PYTHON:
            if func := find_first_ancestor(self.ts_node, ["function_definition"]):
                return self.ctx.node_classes.function_cls(func, self.file_node_id, self.ctx, self.parent)

        return None

    @property
    @reader
    def is_awaited(self) -> bool:
        """Determine if this function call is ultimately awaited in the TypeScript AST.

        This method returns ``True`` if one of the following conditions is met:
          * The call is directly under an ``await_expression`` (i.e., `await foo()`).
          * The call is part of another function call's argument list where that parent call is awaited.
          * The call is inside an arrow function (block or single-expression) that returns it,
            and that arrow function is ultimately passed to an awaited call. The arrow
            function does not need to be marked ``async``.

        Specifically:
          1. The method first checks if the nearest non-parenthesized ancestor is an
             ``await_expression``.
          2. If not, it looks for the nearest parent function call. If there is none,
             the call is not awaited.
          3. If there is a parent call and it is awaited, the method checks whether this
             function call is “returned” (explicitly or implicitly) up the chain toward
             that awaited call.

        Returns:
            bool: ``True`` if this function call is considered awaited (directly or indirectly),
            otherwise ``False``.
        """
        # 1) Direct check: are we directly under an 'await' node?
        ancestor = self.ts_node.parent
        while ancestor and ancestor.type == "parenthesized_expression":
            ancestor = ancestor.parent
        if ancestor and ancestor.type in ("await_expression", "await"):
            return True

        # 2) Find the nearest parent call
        nearest_call = None
        arrow_nodes = []
        is_returned = False

        node = self.ts_node.parent
        while node:
            if node.type in ("call_expression", "call"):
                nearest_call = node
                break

            if node.type == "arrow_function":
                arrow_nodes.append(node)
            elif node.type == "return_statement":
                is_returned = True

            node = node.parent

        if not nearest_call:
            return False

        # 3) Check if the nearest parent call is awaited
        parent_call_obj = FunctionCall(nearest_call, self.file_node_id, self.ctx, None)
        if not parent_call_obj.is_awaited:
            return False

        # If we have no arrow boundaries in between, we're certainly awaited
        if not arrow_nodes:
            return True

        # Otherwise, check if we're effectively returned (explicitly or implicitly) in the arrow callbacks
        if is_returned:
            return True

        for arrow_node in arrow_nodes:
            arrow_body = arrow_node.child_by_field_name("body")
            if arrow_body:
                # Single-expression arrow => implicitly returns the entire expression
                if arrow_body.type != "statement_block":
                    if is_descendant_of(arrow_body, self.ts_node):
                        return True
                # If it's a block body, rely on is_returned above

        return False

    @writer
    def asyncify(self) -> None:
        """Converts the function call to an async function call by wrapping it with 'await'.

        This method adds 'await' syntax to a function call if it is not already awaited. It wraps the function call in parentheses and prefixes it with 'await'.

        Args:
            None

        Returns:
            None
        """
        if self.is_awaited:
            return
        self.insert_before("await (", newline=False)
        self.insert_after(")", newline=False)

    @property
    @reader
    def predecessor(self) -> FunctionCall[Parent] | None:
        """Returns the previous function call in a function call chain.

        Returns the previous function call in a function call chain. This method is useful for traversing function call chains
        to analyze or modify sequences of chained function calls.

        Returns:
            FunctionCall[Parent] | None: The previous function call in the chain, or None if there is no predecessor
            or if the predecessor is not a function call.
        """
        # Recursively travel down the tree to find the previous function call (child nodes are previous calls)
        name = self.get_name()
        while name:
            if isinstance(name, FunctionCall):
                return name
            elif isinstance(name, ChainedAttribute):
                name = name.object
            else:
                break
        return None

    @property
    @reader
    def successor(self) -> FunctionCall[Parent] | None:
        """Returns the next function call in a function call chain.

        Returns the next function call in a function call chain. This method is useful for traversing function call chains
        to analyze or modify sequences of chained function calls.

        Returns:
            FunctionCall[Parent] | None: The next function call in the chain, or None if there is no successor
            or if the successor is not a function call.
        """
        # this will avoid parent function calls in tree-sitter that are NOT part of the chained calls
        if not isinstance(self.parent, ChainedAttribute):
            return None

        return self.parent_of_type(FunctionCall)

    @property
    @noapidoc
    @override
    def viz(self) -> VizNode:
        from codegen.visualizations.enums import VizNode

        func = self.function_definition
        from codegen.sdk.core.function import Function

        if isinstance(func, Function) and func.is_method:
            name = f"{func.parent_class.name}.{self.name}"
            return VizNode(file_path=self.filepath, start_point=self.start_point, end_point=self.end_point, name=name, symbol_name=self.__class__.__name__)
        else:
            return VizNode(file_path=self.filepath, start_point=self.start_point, end_point=self.end_point, name=self.name, symbol_name=self.__class__.__name__)

    @property
    @reader
    def source(self) -> str:
        """Gets the source code representation of this FunctionCall.

        Returns the textual representation of the function call. For chained function calls (e.g., a().b()),
        it returns only the current function call's source code by removing the predecessor's source.

        Args:
            None

        Returns:
            str: The source code representation of this function call. For chained calls, returns only the current
                function call's portion of the chain.
        """
        if self.predecessor:
            # TODO: breaks edit logic b/c start/end bytes no longer match up
            # Remove the parent function call from the source
            return self.extended_source.replace(self.predecessor.extended_source, "").strip()[1:].strip()
        else:
            return self.extended_source

    @property
    @reader
    def args(self) -> Collection[Argument, Self]:
        """Returns a list of arguments passed into the function invocation.

        The `args` property provides access to all arguments, both positional and keyword, that are passed to the function call.

        Args:
            None

        Returns:
            Collection[Argument, Self]: A collection containing the function's arguments.
        """
        # TODO - this may be language-specific
        return self._arg_list

    def set_kwarg(self, name: str, value: str, *, create_on_missing: bool = True, override_existing: bool = True) -> None:
        """Set a keyword argument in a function call.

        Sets or modifies a keyword argument in the function call. Can create new arguments or modify existing ones based on configuration.

        Args:
            name (str): The name of the parameter/argument to set.
            value (str): The value to set the argument to.
            create_on_missing (bool, optional): If True, creates a new keyword argument if it doesn't exist. Defaults to True.
            override_existing (bool, optional): If True, modifies the value of existing argument. Defaults to True.

        Returns:
            None

        Raises:
            None
        """
        if existing := self.get_arg_by_parameter_name(name):
            if not existing.is_named:
                existing.add_keyword(name)
            if override_existing:
                existing.set_value(value)

        elif create_on_missing:
            if param := self.find_parameter_by_name(name):
                # Smart insert into the right place:
                for idx, arg in enumerate(self.args):
                    if other_param := arg.parameter:
                        if other_param.index > param.index:
                            self.args.insert(idx, f"{name}={value}")
                            return
            self.args.append(f"{name}={value}")

    @noapidoc
    @reader
    def find_parameter_by_index(self, index: int) -> Parameter | None:
        from codegen.sdk.python import PyFunction

        for function_definition in self.function_definitions:
            if function_definition.node_type == NodeType.EXTERNAL or function_definition.parameters is None:
                continue

            if isinstance(function_definition, PyFunction) and (function_definition.is_method and not function_definition.is_static_method):
                index += 1
            for param in function_definition.parameters:
                if index == param.index:
                    return param

    @noapidoc
    @reader
    def find_parameter_by_name(self, name: str) -> Parameter | None:
        for function_definition in self.function_definitions:
            if function_definition.node_type == NodeType.EXTERNAL or function_definition.parameters is None:
                continue
            for param in function_definition.parameters:
                if param.name == name:
                    return param

    @reader
    def get_arg_by_parameter_name(self, param_name: str) -> Argument | None:
        """Returns an argument by its parameter name.

        Searches through the arguments of a function call to find an argument that matches
        a specified parameter name. This first checks for named arguments (kwargs) that match
        the parameter name directly, then checks for positional arguments by resolving their
        corresponding parameter names.

        Args:
            param_name (str): The name of the parameter to search for.

        Returns:
            Argument | None: The matching argument if found, None otherwise.
        """
        args = self.args
        if len(args) == 0:
            return None

        # =====[ Named args ]=====
        for arg in args:
            if arg.name == param_name:
                return arg

        for arg in self.args:
            if param := arg.parameter:
                if param.name == param_name:
                    return arg

    @reader
    def get_arg_by_index(self, arg_idx: int) -> Argument | None:
        """Returns the Argument with the given index from the function call's argument list.

        Args:
            arg_idx (int): The index of the argument to retrieve.

        Returns:
            Argument | None: The Argument object at the specified index, or None if the index is out of bounds.
        """
        try:
            return self.args[arg_idx]
        except IndexError:
            return None

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def convert_args_to_kwargs(self, exclude: int = 0) -> None:
        """Converts positional arguments in a function call to keyword arguments.

        This method converts positional arguments to keyword arguments, excluding any leading arguments specified by the exclude parameter.
        This is useful when refactoring function calls to be more explicit and self-documenting.

        Args:
            exclude (int): Number of leading positional arguments to exclude from conversion. Defaults to 0.

        Returns:
            None

        Note:
            - Skips conversion if the argument is already named
            - Skips arguments within the exclude range
            - Skips unpacked arguments (e.g. **kwargs)
            - Stops converting if it encounters a named argument that would conflict with an existing one
            - Requires the function definition to be resolvable and have parameters
        """
        definition = self.function_definition
        from codegen.sdk.core.interfaces.callable import Callable

        if definition is None or definition.parameters is None or not isinstance(definition, Callable):
            return

        for arg in reversed(self.args):
            if arg.is_named:
                # skip if the argument is already named
                continue

            if arg.index < exclude:
                # skip if the argument is in the exclude range
                continue
            if isinstance(arg.value, Unpack):
                # Skip unpack (ie **kwargs)
                continue
            if param := arg.parameter:
                if other_arg := self.get_arg_by_parameter_name(param.name):
                    if other_arg.is_named and other_arg != arg:
                        return  # Already exists, can't keep converting
                arg.add_keyword(param.name)

    @cached_property
    @reader
    @noapidoc
    def function_definition_frames(self) -> list[ResolutionStack[Callable]]:
        from codegen.sdk.core.class_definition import Class
        from codegen.sdk.core.interfaces.callable import Callable

        result = []
        if self.get_name():
            for resolution in self.get_name().resolved_type_frames:
                top_node = resolution.top.node
                if isinstance(top_node, Callable):
                    if isinstance(top_node, Class):
                        if constructor := top_node.constructor:
                            result.append(resolution.with_new_base(constructor, direct=True))
                            continue
                    result.append(resolution)
        return result

    @cached_property
    @reader
    def function_definitions(self) -> list[Callable]:
        """Returns a list of callable objects that could potentially be the target of this function
        call.

        Finds and returns all possible functions that this call could be invoking based on name resolution.
        This is useful for analyzing parameter names, parameter types, and return types of the potential target functions.

        Returns:
            list[Callable]: A list of Callable objects representing the possible function definitions that this call could be invoking.
        """
        result = []
        for frame in self.function_definition_frames:
            result.append(frame.top.node)
        return result

    @property
    @reader
    def function_definition(self) -> Callable | None:
        """Returns the resolved function definition that is being called.

        This method returns the function definition associated with this function call.
        This is useful for accessing parameter names, parameter types, and return types of the called function.

        Returns:
            Callable | None: The resolved function definition, or None if no definition is found.
        """
        return next(iter(self.function_definitions), None)

    @remover
    def remove(self, delete_formatting: bool = True, priority: int = 0, dedupe: bool = True) -> None:
        """Removes a node and optionally its related extended nodes.

        This method removes a FunctionCall node from the codebase. If the node is part of an expression statement,
        it removes the entire expression statement. Otherwise, it performs a standard node removal.

        Args:
            delete_formatting (bool, optional): Whether to delete associated formatting nodes. Defaults to True.
            priority (int, optional): Priority level for the removal operation. Defaults to 0.
            dedupe (bool, optional): Whether to deduplicate identical removals. Defaults to True.

        Returns:
            None
        """
        if self.ts_node.parent.type == "expression_statement":
            Value(self.ts_node.parent, self.file_node_id, self.ctx, self.parent).remove(delete_formatting=delete_formatting, priority=priority, dedupe=dedupe)
        else:
            super().remove(delete_formatting=delete_formatting, priority=priority, dedupe=dedupe)

    @reader
    @noapidoc
    @override
    def _resolved_types(self) -> Generator[ResolutionStack[Self], None, None]:
        from codegen.sdk.core.class_definition import Class
        from codegen.sdk.core.function import Function

        if self.get_name().ts_node.type == "import" or self.full_name == "require":
            # TS imports
            for imp in self.file.imports:
                if imp.ts_node.start_point[0] == self.ts_node.start_point[0]:
                    yield from imp.resolved_type_frames
            return
        if len(self.function_definitions) == 0:
            resolved = False
            for resolution in self.get_name().resolved_type_frames:
                if len(resolution.generics) == 1:
                    yield from self.with_resolution_frame(next(iter(resolution.generics.values())), direct=resolution.direct)
                    resolved = True
                elif len(resolution.generics) > 1:
                    yield from self.with_resolution(resolution)
                    resolved = True
            if not resolved:
                yield ResolutionStack(self)  # This let's us still calculate dependencies even if we can't resolve a function call's definition
        for function_def_frame in self.function_definition_frames:
            function_def = function_def_frame.top.node
            if isinstance(function_def, Function):
                if function_def.is_constructor:
                    yield from self.with_resolution_frame(function_def.parent_class, direct=function_def_frame.direct)
                elif return_type := function_def.return_type:
                    if function_def_frame.generics:
                        if generic := function_def_frame.generics.get(return_type.source, None):
                            yield from self.with_resolution_frame(generic, direct=function_def_frame.direct)
                            return
                    if self.ctx.config.generics:
                        for arg in self.args:
                            if arg.parameter and (type := arg.parameter.type):
                                if type.source == return_type.source:
                                    yield from self.with_resolution_frame(arg.value, direct=function_def_frame.direct)
                                    return
                                if isinstance(type, GenericType):
                                    for param in type.parameters:
                                        if param.source == return_type.source:
                                            yield from self.with_resolution_frame(arg.value, direct=function_def_frame.direct)
                                            return

                    yield from self.with_resolution_frame(return_type, direct=False)
            elif isinstance(function_def, Class):
                yield from self.with_resolution_frame(function_def, direct=function_def_frame.direct, aliased=function_def_frame.aliased)
            #     else:

            #         yield from self.with_resolution_frame(function_def, direct=False)  # Untyped functions
            # else:
            #     yield from self.with_resolution_frame(function_def, direct=False)  # External Modules

    @noapidoc
    def _compute_dependencies(self, usage_type: UsageKind, dest: HasName | None = None) -> None:
        for arg in self.args:
            arg._compute_dependencies(usage_type, dest)
        if desc := self.child_by_field_name("type_arguments"):
            desc._compute_dependencies(UsageKind.GENERIC, dest)
        match = self.get_name()
        if match:
            if len(self.function_definition_frames) > 0:
                if isinstance(match, ChainedAttribute):
                    match.object._compute_dependencies(usage_type, dest)
                if isinstance(match, FunctionCall):
                    match._compute_dependencies(usage_type, dest)
                for definition in self.function_definition_frames:
                    definition.add_usage(self, usage_type, dest, self.ctx)
            else:
                match._compute_dependencies(usage_type, dest)

    @property
    @reader
    def function_calls(self) -> list[FunctionCall]:
        """Returns a list of all function calls contained within this function call.

        This method traverses through all arguments and the function name node to find any nested
        function calls. For example, if a function call has arguments that are themselves function
        calls, these will be included in the returned list.

        Returns:
            list[FunctionCall]: A list of FunctionCall instances contained within this function call,
                including the call itself. Sorted by their appearance in the code.
        """
        calls = [self]
        for arg in self.args:
            calls.extend(arg.function_calls)
        calls.extend(self._name_node.function_calls)
        # for call in self._name_node.function_calls:
        #     if isinstance(call.parent, TSChainedAttribute):
        #         call.parent = self
        #     calls.append(call)
        return sort_editables(calls, dedupe=False)

    @property
    @reader
    def attribute_chain(self) -> list[FunctionCall | Name]:
        """Returns a list of elements in the chainedAttribute that the function call belongs in.

        Breaks down chained expressions into individual components in order of appearance.
        For example: `a.b.c().d` -> [Name("a"), Name("b"), FunctionCall("c"), Name("d")]

        Returns:
            list[FunctionCall | Name]: List of Name nodes (property access) and FunctionCall nodes (method calls)
        """
        if isinstance(self.get_name(), ChainedAttribute):  # child is chainedAttribute. MEANING that this is likely in the middle or the last function call of a chained function call chain.
            return self.get_name().attribute_chain
        elif isinstance(
            self.parent, ChainedAttribute
        ):  # does not have child chainedAttribute, but parent is chainedAttribute. MEANING that this is likely the TOP function call of a chained function call chain.
            return self.parent.attribute_chain
        else:  # this is a standalone function call
            return [self]

    @property
    @noapidoc
    def descendant_symbols(self) -> list[Importable]:
        symbols = self.get_name().descendant_symbols
        for arg in self.args:
            symbols.extend(arg.descendant_symbols)
        return symbols

    @noapidoc
    @writer
    def rename_if_matching(self, old: str, new: str):
        if name := self.get_name():
            name.rename_if_matching(old, new)

    @noapidoc
    def register_api_call(self, url: str):
        assert url, self
        self.ctx.global_context.multigraph.usages[url].append(self)

    @property
    @reader
    def call_chain(self) -> list[FunctionCall]:
        """Returns a list of all function  calls in this function call chain, including this call. Does not include calls made after this one."""
        ret = []

        # backward traversal
        curr = self
        pred = curr.predecessor
        while pred is not None and isinstance(pred, FunctionCall):
            ret.insert(0, pred)
            pred = pred.predecessor

        ret.append(self)

        # forward traversal
        curr = self
        succ = curr.successor
        while succ is not None and isinstance(succ, FunctionCall):
            ret.append(succ)
            succ = succ.successor

        return ret

    @property
    @reader
    def base(self) -> Editable | None:
        """Returns the base object of this function call chain.

        Args:
            Editable | None: The base object of this function call chain.
        """
        name = self.get_name()
        while isinstance(name, ChainedAttribute):
            if isinstance(name.object, FunctionCall):
                return name.object.base
            else:
                name = name.object
        return name

    @property
    @reader
    def promise_chain(self) -> TSPromiseChain | None:
        """Return the promise chain associated with this function call, if a then call is found.

        Returns:
            TSPromiseChain | None: The promise chain associated with this function call, if a then call is found.
        """
        if any(call.name == "then" for call in self.call_chain) is True:
            return TSPromiseChain(self.attribute_chain)
        return None
