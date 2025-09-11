import json
import sys
from decimal import Decimal
from os import PathLike
from pathlib import Path

from rich.console import Console, RenderResult
from rich.syntax import Syntax
from rich.text import Text
from tree_sitter import Node as TSNode
from tree_sitter import Point

from codegen.sdk.output.constants import MAX_EDITABLE_LINES


def style_editable(ts_node: TSNode, filepath: PathLike, file_node: TSNode) -> RenderResult:
    start_line = ts_node.start_point[0] + 1  # 1 based
    start_col = ts_node.start_point[1]
    end_line = ts_node.end_point[0] + 1  # 1 based
    end_col = ts_node.end_point[1]
    truncated = 0
    truncated_len = start_line + MAX_EDITABLE_LINES - 1
    if end_line > truncated_len:
        truncated = end_line - start_line + 1
        for child in ts_node.children:
            if child.end_point[0] + 1 < truncated_len:
                end_line = child.end_point[0] + 1
    syntax = _stylize_range(end_col, end_line, file_node, filepath, start_col, start_line)
    yield syntax
    if truncated:
        yield Text(f"\nTruncated from {truncated} lines")


def _stylize_range(end_col, end_line, file_node, filepath, start_col, start_line):
    syntax = Syntax.from_path(filepath, line_numbers=True, line_range=(start_line, end_line))
    syntax.stylize_range(style="dim", start=(start_line, 0), end=(start_line, start_col))
    syntax.stylize_range(style="dim", start=(end_line, end_col), end=(file_node.end_point[0] + 1, file_node.end_point[1]))
    syntax.stylize_range(style="dim", start=(end_line, end_col), end=(end_line + 1, 0))
    return syntax


def stylize_error(path: PathLike, start: tuple[int, int] | Point, end: tuple[int, int] | Point, file_node: TSNode, content: str, message: str):
    Path(path).write_text(content)
    source = _stylize_range(end[1], end[0] + 1, file_node, path, start[1], start[0] + 1)
    console = Console(file=sys.stderr)
    console.print(f"Syntax Error {message} at:")
    console.print(source)


def safe_getattr(obj, attr, default=None):
    try:
        return getattr(obj, attr, default)
    except (AttributeError, NotImplementedError):
        return default


class DeterministicJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, float):
            return f"{obj:.10f}"
        if isinstance(obj, Decimal):
            return f"{obj:.10f}"
        if isinstance(obj, set):
            return sorted(list(obj))
        if hasattr(obj, "__dict__"):
            return {key: self.default(value) for key, value in obj.__dict__.items()}
        return super().default(obj)


def deterministic_json_dumps(data, **kwargs):
    def sort_dict(item):
        if isinstance(item, dict):
            return {key: sort_dict(value) for key, value in sorted(item.items())}
        elif isinstance(item, list):
            if len(item) > 0 and isinstance(item[0], dict):
                # Sort list of dictionaries based on all keys
                return sorted([sort_dict(i) for i in item], key=lambda x: json.dumps(x, sort_keys=True))
            else:
                return [sort_dict(i) for i in item]
        else:
            return item

    sorted_data = sort_dict(data)
    return json.dumps(sorted_data, cls=DeterministicJSONEncoder, **kwargs)
