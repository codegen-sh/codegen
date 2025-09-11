"""Tool for revealing symbol dependencies and usages."""

from typing import Any, ClassVar, Optional

import tiktoken
from pydantic import Field

from codegen.sdk.ai.utils import count_tokens
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol

from .observation import Observation


class SymbolInfo(Observation):
    """Information about a symbol."""

    name: str = Field(description="Name of the symbol")
    filepath: Optional[str] = Field(description="Path to the file containing the symbol")
    source: str = Field(description="Source code of the symbol")

    str_template: ClassVar[str] = "{name} in {filepath}"


class RevealSymbolObservation(Observation):
    """Response from revealing symbol dependencies and usages."""

    dependencies: Optional[list[SymbolInfo]] = Field(
        default=None,
        description="List of symbols this symbol depends on",
    )
    usages: Optional[list[SymbolInfo]] = Field(
        default=None,
        description="List of symbols that use this symbol",
    )
    truncated: bool = Field(
        default=False,
        description="Whether results were truncated due to token limit",
    )
    valid_filepaths: Optional[list[str]] = Field(
        default=None,
        description="List of valid filepaths when symbol is ambiguous",
    )

    str_template: ClassVar[str] = "Symbol info: {dependencies_count} dependencies, {usages_count} usages"

    def _get_details(self) -> dict[str, Any]:
        """Get details for string representation."""
        return {
            "dependencies_count": len(self.dependencies or []),
            "usages_count": len(self.usages or []),
        }


def truncate_source(source: str, max_tokens: int) -> str:
    """Truncate source code to fit within max_tokens while preserving meaning.

    Attempts to keep the most important parts of the code by:
    1. Keeping function/class signatures
    2. Preserving imports
    3. Keeping the first and last parts of the implementation
    """
    if not max_tokens or max_tokens <= 0:
        return source

    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(source)

    if len(tokens) <= max_tokens:
        return source

    # Split into lines while preserving line endings
    lines = source.splitlines(keepends=True)

    # Always keep first 2 lines (usually imports/signature) and last line (usually closing brace)
    if len(lines) <= 3:
        return source

    result = []
    current_tokens = 0

    # Keep first 2 lines
    for i in range(2):
        line = lines[i]
        line_tokens = len(enc.encode(line))
        if current_tokens + line_tokens > max_tokens:
            break
        result.append(line)
        current_tokens += line_tokens

    # Add truncation indicator
    truncation_msg = "    # ... truncated ...\n"
    truncation_tokens = len(enc.encode(truncation_msg))

    # Keep last line if we have room
    last_line = lines[-1]
    last_line_tokens = len(enc.encode(last_line))

    remaining_tokens = max_tokens - current_tokens - truncation_tokens - last_line_tokens

    if remaining_tokens > 0:
        # Try to keep some middle content
        for line in lines[2:-1]:
            line_tokens = len(enc.encode(line))
            if current_tokens + line_tokens > remaining_tokens:
                break
            result.append(line)
            current_tokens += line_tokens

    result.append(truncation_msg)
    result.append(last_line)

    return "".join(result)


def get_symbol_info(symbol: Symbol, max_tokens: Optional[int] = None) -> SymbolInfo:
    """Get relevant information about a symbol.

    Args:
        symbol: The symbol to get info for
        max_tokens: Optional maximum number of tokens for the source code

    Returns:
        Dict containing symbol metadata and source
    """
    source = symbol.source
    if max_tokens:
        source = truncate_source(source, max_tokens)

    return SymbolInfo(
        status="success",
        name=symbol.name,
        filepath=symbol.file.filepath if symbol.file else None,
        source=source,
    )


def hop_through_imports(symbol: Symbol, seen_imports: Optional[set[str]] = None) -> Symbol:
    """Follow import chain to find the root symbol, stopping at ExternalModule."""
    if seen_imports is None:
        seen_imports = set()

    # Base case: not an import or already seen
    if not isinstance(symbol, Import) or symbol in seen_imports:
        return symbol

    seen_imports.add(symbol.source)

    # Try to resolve the import
    if isinstance(symbol.imported_symbol, ExternalModule):
        return symbol.imported_symbol
    elif isinstance(symbol.imported_symbol, Import):
        return hop_through_imports(symbol.imported_symbol, seen_imports)
    elif isinstance(symbol.imported_symbol, Symbol):
        return symbol.imported_symbol
    else:
        return symbol.imported_symbol


def get_extended_context(
    symbol: Symbol,
    degree: int,
    max_tokens: Optional[int] = None,
    seen_symbols: Optional[set[Symbol]] = None,
    current_degree: int = 0,
    total_tokens: int = 0,
    collect_dependencies: bool = True,
    collect_usages: bool = True,
) -> tuple[list[SymbolInfo], list[SymbolInfo], int]:
    """Recursively collect dependencies and usages up to specified degree.

    Args:
        symbol: The symbol to analyze
        degree: How many degrees of separation to traverse
        max_tokens: Optional maximum number of tokens for all source code combined
        seen_symbols: Set of symbols already processed
        current_degree: Current recursion depth
        total_tokens: Running count of tokens collected
        collect_dependencies: Whether to collect dependencies
        collect_usages: Whether to collect usages

    Returns:
        Tuple of (dependencies, usages, total_tokens)
    """
    if seen_symbols is None:
        seen_symbols = set()

    if current_degree >= degree or symbol in seen_symbols:
        return [], [], total_tokens

    seen_symbols.add(symbol)

    # Get direct dependencies and usages
    dependencies = []
    usages = []

    # Helper to check if we're under token limit
    def under_token_limit() -> bool:
        return not max_tokens or total_tokens < max_tokens

    # Process dependencies
    if collect_dependencies:
        for dep in symbol.dependencies:
            if not under_token_limit():
                break

            dep = hop_through_imports(dep)
            if dep not in seen_symbols:
                # Calculate tokens for this symbol
                info = get_symbol_info(dep, max_tokens=max_tokens)
                symbol_tokens = count_tokens(info.source) if info.source else 0

                if max_tokens and total_tokens + symbol_tokens > max_tokens:
                    continue

                dependencies.append(info)
                total_tokens += symbol_tokens

                if current_degree + 1 < degree:
                    next_deps, next_uses, new_total = get_extended_context(dep, degree, max_tokens, seen_symbols, current_degree + 1, total_tokens, collect_dependencies, collect_usages)
                    dependencies.extend(next_deps)
                    usages.extend(next_uses)
                    total_tokens = new_total

    # Process usages
    if collect_usages:
        for usage in symbol.usages:
            if not under_token_limit():
                break

            usage = usage.usage_symbol
            usage = hop_through_imports(usage)
            if usage not in seen_symbols:
                # Calculate tokens for this symbol
                info = get_symbol_info(usage, max_tokens=max_tokens)
                symbol_tokens = count_tokens(info.source) if info.source else 0

                if max_tokens and total_tokens + symbol_tokens > max_tokens:
                    continue

                usages.append(info)
                total_tokens += symbol_tokens

                if current_degree + 1 < degree:
                    next_deps, next_uses, new_total = get_extended_context(usage, degree, max_tokens, seen_symbols, current_degree + 1, total_tokens, collect_dependencies, collect_usages)
                    dependencies.extend(next_deps)
                    usages.extend(next_uses)
                    total_tokens = new_total

    return dependencies, usages, total_tokens


def reveal_symbol(
    codebase: Codebase,
    symbol_name: str,
    filepath: Optional[str] = None,
    max_depth: Optional[int] = 1,
    max_tokens: Optional[int] = None,
    collect_dependencies: Optional[bool] = True,
    collect_usages: Optional[bool] = True,
) -> RevealSymbolObservation:
    """Reveal the dependencies and usages of a symbol up to N degrees.

    Args:
        codebase: The codebase to analyze
        symbol_name: The name of the symbol to analyze
        filepath: Optional filepath to the symbol to analyze
        max_depth: How many degrees of separation to traverse (default: 1)
        max_tokens: Optional maximum number of tokens for all source code combined
        collect_dependencies: Whether to collect dependencies (default: True)
        collect_usages: Whether to collect usages (default: True)

    Returns:
        Dict containing:
            - dependencies: List of symbols this symbol depends on (if collect_dependencies=True)
            - usages: List of symbols that use this symbol (if collect_usages=True)
            - truncated: Whether the results were truncated due to max_tokens
            - error: Optional error message if the symbol was not found
    """
    symbols = codebase.get_symbols(symbol_name=symbol_name)
    if len(symbols) == 0:
        return RevealSymbolObservation(
            status="error",
            error=f"{symbol_name} not found",
        )
    if len(symbols) > 1:
        return RevealSymbolObservation(
            status="error",
            error=f"{symbol_name} is ambiguous",
            valid_filepaths=[s.file.filepath for s in symbols],
        )
    symbol = symbols[0]
    if filepath:
        if symbol.file.filepath != filepath:
            return RevealSymbolObservation(
                status="error",
                error=f"{symbol_name} not found at {filepath}",
                valid_filepaths=[s.file.filepath for s in symbols],
            )

    # Get dependencies and usages up to specified degree
    dependencies, usages, total_tokens = get_extended_context(symbol, max_depth, max_tokens, collect_dependencies=collect_dependencies, collect_usages=collect_usages)

    was_truncated = max_tokens is not None and total_tokens >= max_tokens

    result = RevealSymbolObservation(
        status="success",
        truncated=was_truncated,
    )
    if collect_dependencies:
        result.dependencies = dependencies
    if collect_usages:
        result.usages = usages
    return result
