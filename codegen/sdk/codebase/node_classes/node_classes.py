from __future__ import annotations

from dataclasses import dataclass, field
from functools import cached_property
from typing import TYPE_CHECKING

from codegen.sdk.core.interfaces.resolvable import Resolvable

if TYPE_CHECKING:
    from codegen.sdk.core.class_definition import Class
    from codegen.sdk.core.detached_symbols.code_block import CodeBlock
    from codegen.sdk.core.detached_symbols.function_call import FunctionCall
    from codegen.sdk.core.detached_symbols.parameter import Parameter
    from codegen.sdk.core.expressions import Expression
    from codegen.sdk.core.expressions.type import Type
    from codegen.sdk.core.file import SourceFile
    from codegen.sdk.core.function import Function
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.interfaces.editable import Editable
    from codegen.sdk.core.statements.comment import Comment
    from codegen.sdk.core.symbol import Symbol


@dataclass
class NodeClasses:
    file_cls: type[SourceFile]
    class_cls: type[Class]
    function_cls: type[Function]
    import_cls: type[Import]

    # Detached symbols
    parameter_cls: type[Parameter]
    code_block_cls: type[CodeBlock]
    function_call_cls: type[FunctionCall]
    comment_cls: type[Comment]
    bool_conversion: dict[bool, str]
    dynamic_import_parent_types: set[type[Editable]]
    symbol_map: dict[str, type[Symbol]] = field(default_factory=dict)
    expression_map: dict[str, type[Expression]] = field(default_factory=dict)
    type_map: dict[str, type[Type] | dict[str, type[Type]]] = field(default_factory=dict)
    keywords: list[str] = field(default_factory=list)
    type_node_type: str = ""
    int_dict_key: bool = False

    @cached_property
    def resolvables(self) -> set[str]:
        id_types = {k for k, v in self.expression_map.items() if isinstance(v, type) and issubclass(v, Resolvable)}
        id_types.update(["identifier"])
        return id_types
