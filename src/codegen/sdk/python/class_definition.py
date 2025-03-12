from typing import Self

from tree_sitter import Node as TSNode

from codegen.sdk.codebase.codebase_context import CodebaseContext
from codegen.sdk.core.autocommit import commiter, reader, writer
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.dataclasses.usage import UsageKind
from codegen.sdk.core.expressions.generic_type import GenericType
from codegen.sdk.core.interfaces.has_name import HasName
from codegen.sdk.core.node_id_factory import NodeId
from codegen.sdk.core.symbol_group import SymbolGroup
from codegen.sdk.core.symbol_groups.multi_line_collection import MultiLineCollection
from codegen.sdk.core.symbol_groups.parents import Parents
from codegen.sdk.extensions.utils import cached_property
from codegen.sdk.python.detached_symbols.code_block import PyCodeBlock
from codegen.sdk.python.detached_symbols.decorator import PyDecorator
from codegen.sdk.python.detached_symbols.parameter import PyParameter
from codegen.sdk.python.expressions.type import PyType
from codegen.sdk.python.function import PyFunction
from codegen.sdk.python.interfaces.has_block import PyHasBlock
from codegen.sdk.python.symbol import PySymbol
from codegen.shared.decorators.docs import noapidoc, py_apidoc


@py_apidoc
class PyClass(Class[PyFunction, PyDecorator, PyCodeBlock, PyParameter, PyType], PyHasBlock, PySymbol):
    """Extends Class for Python codebases

    Attributes:
        constructor_keyword: The keyword used to identify the constructor method in Python classes.
    """

    _decorated_node: TSNode | None
    constructor_keyword = "__init__"

    def __init__(self, ts_node: TSNode, file_id: NodeId, ctx: CodebaseContext, parent: PyHasBlock, decorated_node: TSNode | None = None) -> None:
        super().__init__(ts_node, file_id, ctx, parent)
        self._decorated_node = decorated_node

        if superclasses_node := self.ts_node.child_by_field_name("superclasses"):
            self.parent_classes = Parents(superclasses_node, self.file_node_id, self.ctx, self)
        if self.constructor is not None and len(self.constructor.parameters) > 1:
            self._parameters = SymbolGroup(self.file_node_id, self.ctx, self, children=self.constructor.parameters[1:])
        self.type_parameters = self.child_by_field_name("type_parameters")

    @noapidoc
    @commiter
    def _compute_dependencies(self, usage_type: UsageKind | None = None, dest: HasName | None = None) -> None:
        dest = dest or self.self_dest
        # =====[ Decorated functions ]=====
        for decorator in self.decorators:
            decorator._compute_dependencies(usage_type, dest)

        # =====[ Superclasses ]=====
        # e.g. class A(B, c.D):
        if self.parent_classes is not None:
            self.parent_classes._compute_dependencies(UsageKind.SUBCLASS, dest)
        if self.type_parameters:
            self.type_parameters._compute_dependencies(UsageKind.GENERIC, dest)
        # =====[ Code Block ]=====
        self.code_block._compute_dependencies(usage_type, dest)

    @reader
    def _parse_methods(self) -> MultiLineCollection[PyFunction, Self]:
        methods = [m.symbol for m in self.code_block.symbol_statements if isinstance(m.symbol, PyFunction) and not m.symbol.is_overload]
        block_node = self.code_block.ts_node
        indent_size = block_node.named_children[0].start_point[1]
        if len(methods) > 0:
            # Set start byte at column=0 of first method
            start_byte = methods[0].start_byte - methods[0].start_point[1]
        elif len(self.code_block.statements) > 0:
            # Set start byte at next byte after the last statement in code block
            # Assumption is that the next byte is column=0 of the statement's next line
            start_byte = self.code_block.statements[-1].end_byte + 1
        else:
            # Set start byte at column=0 of start of the code block
            start_byte = block_node.start_byte - block_node.start_point[1]
        return MultiLineCollection(children=methods, file_node_id=self.file_node_id, ctx=self.ctx, parent=self, node=self.code_block.ts_node, indent_size=indent_size, start_byte=start_byte)

    ####################################################################################################################
    # MANIPULATIONS
    ####################################################################################################################

    @writer
    def add_source(self, source: str) -> None:
        """Adds source code to the class definition.

        Adds the provided source code string to the body of the class definition. The method handles
        proper indentation of the source code within the class body.

        Args:
            source (str): The source code to be added to the class definition. If the source doesn't
                start with a newline, it will be indented with 4 spaces.

        Raises:
            ValueError: If the class body cannot be found.
        """
        class_body = self.child_by_field_name("body")
        if class_body is None:
            msg = "Could not find class body"
            raise ValueError(msg)
        # Mimic previous behaviour
        source = source if source.startswith("\n") else "    " + source
        # TODO: use real fix_indentation behaviour
        class_body.insert_after("\n" + source, fix_indentation=False, newline=False)

    @cached_property
    @noapidoc
    def generics(self) -> dict[str, PyType]:
        ret = super().generics
        if self.parent_classes:
            for supercls in self.parent_classes:
                if isinstance(supercls, GenericType):
                    if supercls.name == "Generic":
                        for param in supercls.parameters:
                            ret[param.name] = param
        return ret
