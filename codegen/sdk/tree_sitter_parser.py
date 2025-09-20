import os
from os import PathLike
from pathlib import Path
from typing import Union

import tree_sitter_javascript as ts_javascript
import tree_sitter_python as ts_python
import tree_sitter_typescript as ts_typescript
from tree_sitter import Language, Parser
from tree_sitter import Node as TSNode

from codegen.sdk.output.utils import stylize_error

PY_LANGUAGE = Language(ts_python.language())
JS_LANGUAGE = Language(ts_javascript.language())
TS_LANGUAGE = Language(ts_typescript.language_typescript())
TSX_LANGUAGE = Language(ts_typescript.language_tsx())


def to_extension(filepath_or_extension: str | PathLike) -> str:
    return Path(filepath_or_extension).suffix


class _TreeSitterAbstraction:
    """Class to facilitate loading/retrieval of the Parser object for a given language.
    Should not be used directly, instead use `get_tree_sitter_parser` to get the parser for a given extension.
    """

    _instance: Union["_TreeSitterAbstraction", None] = None
    # TODO: use ProgrammingLanguages enum here instead
    extension_to_lang = {
        # ".js": JS_LANGUAGE,
        # ".jsx": JS_LANGUAGE,
        # ".ts": TS_LANGUAGE,
        # Use TSX for ALL JS/TS files!
        ".js": TSX_LANGUAGE,
        ".jsx": TSX_LANGUAGE,
        ".ts": TSX_LANGUAGE,
        ".tsx": TSX_LANGUAGE,
        ".py": PY_LANGUAGE,
    }
    extension_to_parser: dict[str, Parser] = {}

    def __init__(self) -> None:
        self.initialize_parsers()

    def initialize_parsers(self) -> None:
        for extension, language in self.extension_to_lang.items():
            parser = Parser(language)
            self.extension_to_parser[extension] = parser


_ts_parser_factory = _TreeSitterAbstraction()


def get_parser_by_filepath_or_extension(filepath_or_extension: str | PathLike = ".py") -> Parser:
    extension = to_extension(filepath_or_extension)
    # HACK: we do not currently use a plain text parser, so default to python for now
    if extension not in _ts_parser_factory.extension_to_parser:
        extension = ".py"
    return _ts_parser_factory.extension_to_parser[extension]


def get_lang_by_filepath_or_extension(filepath_or_extension: str = ".py") -> Language:
    extension = to_extension(filepath_or_extension)
    # HACK: we do not currently use a plain text parser, so default to python for now
    if extension not in _ts_parser_factory.extension_to_parser:
        extension = ".py"
    return _ts_parser_factory.extension_to_lang[extension]


def parse_file(filepath: PathLike, content: str) -> TSNode:
    parser = get_parser_by_filepath_or_extension(filepath)
    ts_node = parser.parse(bytes(content, "utf-8")).root_node
    return ts_node


def print_errors(filepath: PathLike, content: str) -> None:
    if not os.path.exists(filepath):
        return
    parser = get_parser_by_filepath_or_extension(filepath)
    ts_node = parser.parse(bytes(content, "utf-8")).root_node
    if ts_node.has_error:

        def traverse(node):
            if node.is_error or node.is_missing:
                stylize_error(filepath, node.start_point, node.end_point, ts_node, content, "with ts_node type of " + node.type)
            if node.has_error:
                for child in node.children:
                    traverse(child)

        traverse(ts_node)
