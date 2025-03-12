from lsprotocol.types import DocumentSymbol

from codegen.extensions.lsp.kind import get_kind
from codegen.extensions.lsp.range import get_range
from codegen.sdk.core.class_definition import Class
from codegen.sdk.core.interfaces.editable import Editable
from codegen.sdk.extensions.sort import sort_editables


def get_document_symbol(node: Editable) -> DocumentSymbol:
    children = []
    nodes = []
    if isinstance(node, Class):
        nodes.extend(node.methods)
        nodes.extend(node.attributes)
        nodes.extend(node.nested_classes)
    nodes = sort_editables(nodes)
    for child in nodes:
        children.append(get_document_symbol(child))
    return DocumentSymbol(
        name=node.name,
        kind=get_kind(node),
        range=get_range(node),
        selection_range=get_range(node.get_name()),
        children=children,
    )
