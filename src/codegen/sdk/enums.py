from enum import IntEnum, auto
from typing import NamedTuple

from codegen.sdk.core.dataclasses.usage import Usage
from codegen.shared.decorators.docs import apidoc


class NodeType(IntEnum):
    """NodeType is an enumeration class that defines different types of nodes within the graph."""

    REPO = auto()  # Node representing the full repository
    FILE = auto()  # Node representing a file
    IMPORT = auto()  # Node representing an import statement
    EXPORT = auto()  # Node representing an export statement
    SYMBOL = auto()  # Node representing a symbol defined in a file
    EXTERNAL = auto()  # Node representing something external to the codebase, e.g. `datetime`
    EXPRESSION = auto()  # Node representing an expression within a statement.


class FileGraphNodeType(IntEnum):
    # File graph nodes
    STATEMENT = auto()  # Node representing a statement in code block.
    EXPRESSION = auto()  # Node representing an expression within a statement.


class FileGraphEdgeType(IntEnum):
    # File graph edges
    STATEMENT_CONTAINS_EXPRESSION = auto()  # Edge from statement to expression.


class EdgeType(IntEnum):
    # === [ External Edges Between Files ] ===
    # Edge from Import => resolved Symbol.
    # Should be added by the import, only after all the files have been parsed.
    IMPORT_SYMBOL_RESOLUTION = auto()
    EXPORT = auto()
    SUBCLASS = auto()
    # Edge from Symbol => used Symbol (or Import) referenced within the same file.
    # Should be added by the parent symbol, only after all the file children node types have been added to the graph.
    SYMBOL_USAGE = auto()


class SymbolType(IntEnum):
    """TODO: names should be all uppercase"""

    Function = auto()
    Class = auto()
    GlobalVar = auto()
    Interface = auto()
    Type = auto()
    Enum = auto()
    Namespace = auto()


@apidoc
class ImportType(IntEnum):
    """Import types for each import object. Determines what the import resolves to, and what symbols are imported.

    Attributes:
        DEFAULT_EXPORT: Imports all default exports. Resolves to the file.
        NAMED_EXPORT: Imports a named export. Resolves to the symbol export.
        WILDCARD: Imports all named exports, and default exports as `default`. Resolves to the file.
        MODULE: Imports the module, not doesn't actually allow access to any of the exports
        SIDE_EFFECT: Imports the module, not doesn't actually allow access to any of the exports
        UNKNOWN: Unknown import type.
    """

    # Imports all default exports. Resolves to the file.
    DEFAULT_EXPORT = auto()
    # Imports a named export. Resolves to the symbol export.
    NAMED_EXPORT = auto()
    # Imports all named exports, and default exports as `default`. Resolves to the file.
    WILDCARD = auto()
    # Imports all default and named exports. The default export is aliased as `default` and can be accessed by `moduleName.default`
    # Resolves to the file.
    MODULE = auto()
    # Imports the module, not doesn't actually allow access to any of the exports
    # Resolves to the file.
    SIDE_EFFECT = auto()
    UNKNOWN = auto()  # TODO: get rid of this - mostly used to set default value. we should just set to None.


class Edge(NamedTuple):
    type: EdgeType
    usage: Usage | None
