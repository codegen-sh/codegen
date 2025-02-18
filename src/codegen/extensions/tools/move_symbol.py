"""Tool for moving symbols between files."""

from typing import Any, Literal

from codegen import Codebase

from .view_file import view_file


def move_symbol(
    codebase: Codebase,
    source_file: str,
    symbol_name: str,
    target_file: str,
    strategy: Literal["update_all_imports", "add_back_edge"] = "update_all_imports",
    include_dependencies: bool = True,
) -> dict[str, Any]:
    """Move a symbol from one file to another.

    Args:
        codebase: The codebase to operate on
        source_file: Path to the file containing the symbol
        symbol_name: Name of the symbol to move
        target_file: Path to the destination file
        strategy: Strategy for handling imports:
                 - "update_all_imports": Updates all import statements across the codebase (default)
                 - "add_back_edge": Adds import and re-export in the original file
        include_dependencies: Whether to move dependencies along with the symbol

    Returns:
        Dict containing move status and updated file info, or error information if operation fails
    """
    try:
        source = codebase.get_file(source_file)
    except ValueError:
        return {"error": f"Source file not found: {source_file}"}
    if source is None:
        return {"error": f"Source file not found: {source_file}"}

    try:
        target = codebase.get_file(target_file)
    except ValueError:
        return {"error": f"Target file not found: {target_file}"}

    symbol = source.get_symbol(symbol_name)
    if not symbol:
        return {"error": f"Symbol '{symbol_name}' not found in {source_file}"}

    try:
        symbol.move_to_file(target, include_dependencies=include_dependencies, strategy=strategy)
        codebase.commit()
        return {
            "status": "success",
            "symbol": symbol_name,
            "source_file": source_file,
            "target_file": target_file,
            "source_file_info": view_file(codebase, source_file),
            "target_file_info": view_file(codebase, target_file),
        }
    except Exception as e:
        return {"error": f"Failed to move symbol: {e!s}"}
