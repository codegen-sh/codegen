import tree_sitter
from lsprotocol.types import Position, Range
from pygls.workspace import TextDocument

from codegen.sdk.core.interfaces.editable import Editable


def get_range(node: Editable) -> Range:
    start_point = node.start_point
    end_point = node.end_point
    for extended_node in node.extended_nodes:
        if extended_node.start_point.row < start_point.row:
            start_point = extended_node.start_point
        if extended_node.end_point.row > end_point.row:
            end_point = extended_node.end_point
    return Range(
        start=Position(line=start_point.row, character=start_point.column),
        end=Position(line=end_point.row, character=end_point.column),
    )


def get_tree_sitter_range(range: Range, document: TextDocument) -> tree_sitter.Range:
    start_pos = tree_sitter.Point(row=range.start.line, column=range.start.character)
    end_pos = tree_sitter.Point(row=range.end.line, column=range.end.character)
    start_byte = document.offset_at_position(range.start)
    end_byte = document.offset_at_position(range.end)
    return tree_sitter.Range(
        start_point=start_pos,
        end_point=end_pos,
        start_byte=start_byte,
        end_byte=end_byte,
    )
