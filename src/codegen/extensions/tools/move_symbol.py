"""Tool for moving symbols between files."""

from typing import ClassVar, Literal

from pydantic import Field

from codegen.sdk.core.codebase import Codebase

from .observation import Observation
from .view_file import ViewFileObservation, view_file


class MoveSymbolObservation(Observation):
    """Response from moving a symbol between files."""

    symbol_name: str = Field(
        description="Name of the symbol that was moved",
    )
    source_file: str = Field(
        description="Path to the source file",
    )
    target_file: str = Field(
        description="Path to the target file",
    )
    source_file_info: ViewFileObservation = Field(
        description="Information about the source file after move",
    )
    target_file_info: ViewFileObservation = Field(
        description="Information about the target file after move",
    )

    str_template: ClassVar[str] = "Moved symbol {symbol_name} from {source_file} to {target_file}"


def move_symbol(
    codebase: Codebase,
    source_file: str,
    symbol_name: str,
    target_file: str,
    strategy: Literal["update_all_imports", "add_back_edge"] = "update_all_imports",
    include_dependencies: bool = True,
) -> MoveSymbolObservation:
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
        MoveSymbolObservation containing move status and updated file info
    """
    try:
        source = codebase.get_file(source_file)
    except ValueError:
        return MoveSymbolObservation(
            status="error",
            error=f"Source file not found: {source_file}",
            symbol_name=symbol_name,
            source_file=source_file,
            target_file=target_file,
            source_file_info=ViewFileObservation(
                status="error",
                error=f"Source file not found: {source_file}",
                filepath=source_file,
                content="",
                line_count=0,
            ),
            target_file_info=ViewFileObservation(
                status="error",
                error=f"Source file not found: {source_file}",
                filepath=target_file,
                content="",
                line_count=0,
            ),
        )

    try:
        target = codebase.get_file(target_file)
    except ValueError:
        return MoveSymbolObservation(
            status="error",
            error=f"Target file not found: {target_file}",
            symbol_name=symbol_name,
            source_file=source_file,
            target_file=target_file,
            source_file_info=ViewFileObservation(
                status="error",
                error=f"Target file not found: {target_file}",
                filepath=source_file,
                content="",
                line_count=0,
            ),
            target_file_info=ViewFileObservation(
                status="error",
                error=f"Target file not found: {target_file}",
                filepath=target_file,
                content="",
                line_count=0,
            ),
        )

    symbol = source.get_symbol(symbol_name)
    if not symbol:
        return MoveSymbolObservation(
            status="error",
            error=f"Symbol '{symbol_name}' not found in {source_file}",
            symbol_name=symbol_name,
            source_file=source_file,
            target_file=target_file,
            source_file_info=view_file(codebase, source_file),
            target_file_info=view_file(codebase, target_file),
        )

    try:
        symbol.move_to_file(target, include_dependencies=include_dependencies, strategy=strategy)
        codebase.commit()

        return MoveSymbolObservation(
            status="success",
            symbol_name=symbol_name,
            source_file=source_file,
            target_file=target_file,
            source_file_info=view_file(codebase, source_file),
            target_file_info=view_file(codebase, target_file),
        )
    except Exception as e:
        return MoveSymbolObservation(
            status="error",
            error=f"Failed to move symbol: {e!s}",
            symbol_name=symbol_name,
            source_file=source_file,
            target_file=target_file,
            source_file_info=view_file(codebase, source_file),
            target_file_info=view_file(codebase, target_file),
        )
