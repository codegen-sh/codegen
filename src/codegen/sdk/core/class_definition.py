from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Generic, Literal, Self, overload, override

from typing_extensions import TypeVar

from codegen.sdk._proxy import proxy_property
from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.interfaces.callable import Callable
from codegen.sdk.core.interfaces.has_attribute import HasAttribute
from codegen.sdk.core.interfaces.has_block import HasBlock
from codegen.sdk.core.interfaces.inherits import Inherits
from codegen.sdk.core.statements.attribute import Attribute
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.core.symbol import Symbol
from codegen.sdk.enums import SymbolType
from codegen.sdk.extensions.utils import cached_property
from codegen.shared.decorators.docs import apidoc, noapidoc
from codegen.shared.logging.get_logger import get_logger
from codegen.visualizations.enums import VizNode

if TYPE_CHECKING:
    from tree_sitter import Node as TSNode

    from codegen.sdk.codebase.codebase_context import CodebaseContext
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.decorator import Decorator
    from codegen.sdk.core.detached_symbols.parameter import Parameter
    from codegen.sdk.core.expressions import Name
    from codegen.sdk.core.expressions.chained_attribute import ChainedAttribute
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.external_module import ExternalModule
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.interface import Interface
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.node_id_factory import NodeId
    from codegen.sdk.core.statements.symbol_statement import SymbolStatement
    from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection
    from codegen.sdk.core.symbol_groups.parents import Parents


logger = get_logger(__name__)


TFunction = TypeVar("TFunction", bound="Function", default="Function")
TDecorator = TypeVar("TDecorator", bound="Decorator", default="Decorator")
TCodeBlock = TypeVar("TCodeBlock", bound="CodeBlock", default="CodeBlock")
TParameter = TypeVar("TParameter", bound="Parameter", default="Parameter")
TType = TypeVar("TType", bound="Type", default="Type")


@apidoc
class Class(Inherits[TType], HasBlock[TCodeBlock, TDecorator], Callable[TParameter, TType], HasAttribute[TFunction | Attribute], Generic[TFunction, TDecorator, TCodeBlock, TParameter, TType]):
    """Abstract representation of a Class definition.

    Attributes:
        symbol_type: The type of symbol, set to SymbolType.Class.
        constructor_keyword: The keyword used to identify the constructor method.
        parent_classes: The parent classes of this class, if any.
    """

    symbol_type = SymbolType.Class
    constructor_keyword = None
    parent_classes: Parents[TType, Self] | None = None
    _methods: MultiLineCollection[TFunction, Self] | None = None

    def __init__(self, ts_node: TSNode, file_id: NodeId, ctx: CodebaseContext, parent: SymbolStatement) -> None:
        super().__init__(ts_node, file_id, ctx, parent)
        self._methods = self._parse_methods()
        self._parameters = []

    ####################################################################################################################
    # PROPERTIES
    ####################################################################################################################
    @proxy_property
    @reader
    def superclasses(self, max_depth: int | None = None) -> list[Class | ExternalModule | Interface]:
        """Returns a list of all classes that this class extends, up to max_depth.

        Gets all classes that this class extends, traversing up the inheritance tree up to max_depth.
        The traversal follows Python's Method Resolution Order (MRO), meaning superclasses are searched breadth-first.

        Args:
            max_depth (int | None): The maximum depth to traverse up the inheritance tree. If None, traverses the entire tree.

        Returns:
            list[Class | ExternalModule | Interface]: A list of all superclass symbols in MRO order, up to max_depth.
            Returns an empty list if the class has no parent classes.
        """
        # Implements the python MRO, IE: by level
        if self.parent_classes is not None:
            return self._get_superclasses(max_depth=max_depth)
        return []

    @property
    @reader
    def parent_class_names(self) -> list[Name | ChainedAttribute]:
        """Returns a list of the parent class names that this class inherits from.

        Gets the list of parent class names from Parents object. Returns empty list if class has no parents.

        Returns:
            list[Name | ChainedAttribute]: A list of parent class identifiers. Each identifier can be either a simple
                name (Name) or a chained attribute (e.g., 'module.Class').
        """
        if self.parent_classes:
            return self.parent_classes.parent_class_names
        return []

    @reader
    def get_parent_class(self, parent_class_name: str) -> Editable | None:
        """Returns the parent class node with the specified name.

        Retrieves a parent class Name or ChainedAttribute node from this class's list of parent class names that matches
        the specified name.

        Args:
            parent_class_name (str): The name of the parent class to find.

        Returns:
            Editable | None: The matching parent class node, or None if no match is found.
        """
        return next((p for p in self.parent_class_names if p.source == parent_class_name), None)

    @property
    @reader
    def is_subclass(self) -> bool:
        """Indicates whether the current class is a subclass of another class.

        A class is considered a subclass if it inherits from at least one parent class.

        Returns:
            bool: True if the class has one or more parent classes, False otherwise.
        """
        return len(self.parent_class_names) > 0

    @reader
    def is_subclass_of(self, parent_class: str | Class, max_depth: int | None = None) -> bool:
        """Checks if the class inherits from a specified parent class.

        Determines whether this class is a subclass (direct or indirect) of the specified parent class. The search can be limited to a certain depth in the inheritance tree.

        Args:
            parent_class (str | Class): The parent class to check for. Can be specified either as a class name string or Class object.
            max_depth (int | None): Maximum inheritance depth to search. None means no limit.

        Returns:
            bool: True if this class inherits from the parent class, False otherwise.
        """
        if self.parent_classes is None:
            return False
        return self.parent_classes.is_subclass_of(parent_class, max_depth=max_depth)

    @proxy_property
    @reader
    def subclasses(self, max_depth: int | None = None) -> list[Class]:
        """Returns all classes which subclass this class.

        Retrieves a list of all classes in the codebase that inherit from this class, up to a specified depth.

        Args:
            max_depth (int | None, optional): Maximum inheritance depth to search. If None, searches all depths. Defaults to None.

        Returns:
            list[Class]: A list of Class objects that inherit from this class.
        """
        return self._get_subclasses(max_depth)

    @noapidoc
    @commiter
    def compute_superclass_dependencies(self) -> None:
        if self.parent_classes:
            self.parent_classes.compute_superclass_dependencies()

    @cached_property
    @reader
    def constructor(self) -> TFunction | None:
        """Returns the constructor method for this class.

        Gets the constructor of the class (e.g., __init__ in Python) by checking for a method matching the class's constructor_keyword. This includes searching through superclasses.

        Returns:
            TFunction | None: The constructor method if found, None otherwise.
        """
        # This now does the superclass traversal
        return self.get_method(self.constructor_keyword)

    @abstractmethod
    @reader
    def _parse_methods(self) -> MultiLineCollection[TFunction, Self]:
        """Parses the methods of the class into a multi line collection."""

    @overload
    def methods(self, *, max_depth: Literal[0] = ..., private: Literal[True] = ..., magic: Literal[True] = ...) -> MultiLineCollection[TFunction, Self]: ...
    @overload
    def methods(self, *, max_depth: int | None = ..., private: bool = ..., magic: Literal[False]) -> list[TFunction]: ...
    @overload
    def methods(self, *, max_depth: int | None = ..., private: Literal[False], magic: bool = ...) -> list[TFunction]: ...
    @overload
    def methods(self, *, max_depth: int | None, private: bool = ..., magic: bool = ...) -> list[TFunction]: ...
    @proxy_property
    @reader
    def methods(self, *, max_depth: int | None = 0, private: bool = True, magic: bool = True) -> list[TFunction] | MultiLineCollection[TFunction, Self]:
        """Retrieves all methods that exist on this Class, including methods from superclasses, with
        filtering options.

        Args:
            max_depth (int | None, optional): Include parent classes up to max_depth. None means no limit, 0 means only current class. Defaults to 0.
            private (bool, optional): Whether to include private methods. Defaults to True.
            magic (bool, optional): Whether to include magic methods. Defaults to False.

        Returns:
            A list of methods that match the filtering criteria. Methods are ordered by class hierarchy
                (methods from the current class appear before methods from parent classes). For methods with the same name,
                only the first occurrence is included. Methods are returned as a MultiLineCollection for efficient access and manipulation if max depth is 0 and private and magic methods
                are included.
        """
        if max_depth == 0 and private and magic:
            return self._methods
        parents = [self, *self.superclasses(max_depth=max_depth)]
        result = {}
        for c in parents:
            if isinstance(c, Class):
                for m in c._methods:
                    if m.is_private and not private:
                        continue
                    if m.is_magic and not magic:
                        continue
                    if m.name not in result:
                        result[m.name] = m
        return list(result.values())

    @reader
    def get_nested_class(self, name: str) -> Self | None:
        """Returns a nested class by name from the current class.

        Searches through the nested classes defined in the class and returns the first one that matches the given name.

        Args:
            name (str): The name of the nested class to find.

        Returns:
            Self | None: The nested class if found, None otherwise.
        """
        for m in self.nested_classes:
            if m.name == name:
                return m
        return None

    @reader
    def get_method(self, name: str) -> TFunction | None:
        """Returns a specific method by name from the class or any of its superclasses.

        Searches through the class's methods and its superclasses' methods to find a method with the specified name.

        Args:
            name (str): The name of the method to find.

        Returns:
            TFunction | None: The method if found, None otherwise.
        """
        parents = [self, *self.superclasses]
        for c in parents:
            if isinstance(c, Class):
                for m in c.methods:
                    if m.name == name:
                        return m
        return None

    @proxy_property
    @reader
    def attributes(self, *, max_depth: int | None = 0, private: bool = True) -> list[Attribute]:
        """Retrieves all attributes from this Class including those from its superclasses up to a
        specified depth.

        Args:
            max_depth (int | None): The maximum depth of superclass traversal. None means no limit, 0 means only this class.
            private (bool): Whether to include private attributes. Defaults to True.

        Returns:
            list[Attribute]: A list of unique attributes from this class and its superclasses. If an attribute is defined in
                            multiple classes, the first definition encountered is used.
        """
        parents = [self, *self.superclasses(max_depth=max_depth)]
        result = {}
        for c in parents:
            if isinstance(c, Class):
                for m in c.code_block.get_attributes(private):
                    if m.name not in result:
                        result[m.name] = m
        return list(result.values())

    @reader
    def get_attribute(self, name: str) -> Attribute | None:
        """Returns a specific attribute by name.

        Searches for an attribute with the given name in the current class and its superclasses.

        Args:
            name (str): The name of the attribute to search for.

        Returns:
            Attribute | None: The matching attribute if found, None otherwise. If multiple attributes with the same name exist in the inheritance hierarchy, returns the first one found.
        """
        parents = [self, *self.superclasses]
        for c in parents:
            if isinstance(c, Class):
                for m in c.code_block.get_attributes(name):
                    if m.name == name:
                        return m
        return None

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @abstractmethod
    def add_source(self, source: str) -> None:
        """Add a block of source code to the bottom of a class definition.

        Adds the provided source code to the end of the class definition, after all existing methods and attributes.

        Args:
            source (str): The source code to be added to the class definition. The code should be properly formatted
                for class-level insertion.

        Returns:
            None
        """

    @writer
    def add_attribute_from_source(self, source: str) -> None:
        """Adds an attribute to a class from raw source code, placing it in a specific location
        based on the class structure.

        This method intelligently places the new attribute after existing attributes and docstrings but before methods to maintain a clean class structure.

        Args:
            source (str): The source code of the attribute to be added.

        Returns:
            None
        """
        attributes = self.attributes
        if len(attributes) > 0:
            last_attribute = attributes[-1]
            last_attribute.insert_after(source, fix_indentation=True)
        elif (methods := self.methods) and len(methods) > 0:
            first_method = methods[0]
            first_method.insert_before(f"{source}\n", fix_indentation=True)
        elif len(self.code_block.statements) > 0:
            first_statement = self.code_block.statements[0]
            first_statement.insert_before(source, fix_indentation=True)
        else:
            self.code_block.insert_after(source, fix_indentation=True)

    @writer
    def add_attribute(self, attribute: Attribute, include_dependencies: bool = False) -> None:
        """Adds an attribute to a class from another class.

        This method adds an attribute to a class, optionally including its dependencies. If dependencies are included, it will add any necessary imports to the class's file.

        Args:
            attribute (Attribute): The attribute to add to the class.
            include_dependencies (bool, optional): Whether to include the attribute's dependencies. If True, adds any necessary imports to the class's file. Defaults to False.

        Returns:
            None
        """
        # TODO: maybe this should be on Attribute API and renamed to "move_to_class"
        # - my preference is to drop it altogether, or combine with add_attribute_from_source
        self.add_attribute_from_source(attribute.source)

        if include_dependencies:
            deps = attribute.dependencies
            file = self.file
            for d in deps:
                if isinstance(d, Import):
                    file.add_import(d.imported_symbol)
                elif isinstance(d, Symbol):
                    file.add_import(d)

    @property
    @noapidoc
    def viz(self) -> VizNode:
        return VizNode(file_path=self.filepath, start_point=self.start_point, end_point=self.end_point, name=self.name, symbol_name=self.__class__.__name__)

    @noapidoc
    @reader
    @override
    def resolve_attribute(self, name: str) -> Attribute | TFunction | None:
        if method := self.get_method(name):
            return method
        if attr := self.get_attribute(name):
            return attr
        for c in [self, *self.superclasses]:
            if isinstance(c, Class):
                for child_class in c.nested_classes:
                    if child_class.name == name:
                        return child_class

    @property
    def nested_classes(self) -> list[Self]:
        """Retrieves the nested classes defined within this class.

        Args:
            None

        Returns:
            list[Self]: A list of Class objects representing nested class definitions within this class.
        """
        symbols = []
        for s in self.code_block.statements:
            if s.statement_type == StatementType.SYMBOL_STATEMENT:
                if (c := s.symbol) and isinstance(c, Class):
                    symbols.append(c)
        return symbols
