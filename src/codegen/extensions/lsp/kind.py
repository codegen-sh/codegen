from lsprotocol.types import SymbolKind

from codegen.sdk.core.assignment import Assignment
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.file import File
from codegen.sdk.core.function import Function
from codegen.sdk.core.interface import Interface
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.core.statements.attribute import Attribute
from codegen.sdk.typescript.namespace import TSNamespace

kinds = {
    File: SymbolKind.File,
    Class: SymbolKind.Class,
    Function: SymbolKind.Function,
    Assignment: SymbolKind.Variable,
    Interface: SymbolKind.Interface,
    TSNamespace: SymbolKind.Namespace,
    Attribute: SymbolKind.Variable,
}


def get_kind(node: Editable) -> SymbolKind:
    if isinstance(node, Function):
        if node.is_method:
            return SymbolKind.Method
    for kind in kinds:
        if isinstance(node, kind):
            return kinds[kind]
    msg = f"No kind found for {node}, {type(node)}"
    raise ValueError(msg)
