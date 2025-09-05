"""Utilities to prevent circular imports."""

from typing import TYPE_CHECKING, Any, TypeGuard, Union

if TYPE_CHECKING:
    from codegen.sdk.core.file import File
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.symbol import Symbol


def is_file(node: Any) -> TypeGuard["File"]:
    from codegen.sdk.core.file import File

    return isinstance(node, File)


def is_symbol(node: Any) -> TypeGuard["Symbol"]:
    from codegen.sdk.core.symbol import Symbol

    return isinstance(node, Symbol)


def is_on_graph(node: Any) -> TypeGuard[Union["Import", "Symbol"]]:
    from codegen.sdk.core.import_resolution import Import
    from codegen.sdk.core.symbol import Symbol

    return isinstance(node, Import | Symbol)
