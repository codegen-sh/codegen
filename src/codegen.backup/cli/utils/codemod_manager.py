import builtins
from pathlib import Path

import rich
import typer

from codegen.cli.utils.function_finder import DecoratedFunction, find_codegen_functions


def _might_have_decorators(file_path: Path) -> bool:
    """Quick check if a file might contain codegen decorators.

    This is a fast pre-filter that checks if '@codegen' appears anywhere in the file.
    Much faster than parsing the AST for files that definitely don't have decorators.
    """
    try:
        # Read in binary mode and check for b'@codegen' to handle any encoding
        with open(file_path, "rb") as f:
            return b"@codegen" in f.read()
    except Exception:
        return False


class CodemodManager:
    """Manages codemod operations in the local filesystem."""

    @staticmethod
    def get_valid_name(name: str) -> str:
        return name.lower().replace(" ", "_").replace("-", "_")

    @classmethod
    def get_codemod(cls, name: str, start_path: Path | None = None) -> DecoratedFunction:
        """Get and validate a codemod by name.

        Args:
            name: Name of the codemod to find
            start_path: Directory to start searching from (default: current directory)

        Returns:
            The validated DecoratedFunction

        Raises:
            typer.Exit: If codemod can't be found or loaded
        """
        # First try to find the codemod
        codemod = cls.get(name, start_path)
        if not codemod:
            # If not found, check if any codemods exist
            all_codemods = cls.list(start_path)
            if not all_codemods:
                rich.print("[red]Error:[/red] No codemods found. Create one with:")
                rich.print("  codegen create my-codemod")
                raise typer.Exit(1)
            else:
                available = "\n  ".join(f"- {c.name}" for c in all_codemods)
                rich.print(f"[red]Error:[/red] Codemod '{name}' not found. Available codemods:")
                rich.print(f"  {available}")
                raise typer.Exit(1)

        # Verify we can import it
        try:
            # This will raise ValueError if function can't be imported
            codemod.validate()
            return codemod
        except Exception as e:
            rich.print(f"[red]Error:[/red] Error loading codemod '{name}': {e!s}")
            raise typer.Exit(1)

    @classmethod
    def list(cls, start_path: Path | None = None) -> builtins.list[DecoratedFunction]:
        """List all codegen decorated functions in Python files under the given path.

        This is an alias for get_decorated for better readability.
        """
        return cls.get_decorated(start_path)

    @classmethod
    def get(cls, name: str, start_path: Path | None = None) -> DecoratedFunction | None:
        """Get a specific codegen decorated function by name.

        Args:
            name: Name of the function to find (case-insensitive, spaces/hyphens converted to underscores)
            start_path: Directory or file to start searching from. Defaults to current working directory.

        Returns:
            The DecoratedFunction if found, None otherwise

        """
        valid_name = cls.get_valid_name(name)
        functions = cls.get_decorated(start_path)

        for func in functions:
            if cls.get_valid_name(func.name) == valid_name:
                return func
        return None

    @classmethod
    def exists(cls, name: str, start_path: Path | None = None) -> bool:
        """Check if a codegen decorated function with the given name exists.

        Args:
            name: Name of the function to check (case-insensitive, spaces/hyphens converted to underscores)
            start_path: Directory or file to start searching from. Defaults to current working directory.

        Returns:
            True if the function exists, False otherwise

        """
        return cls.get(name, start_path) is not None

    @classmethod
    def get_decorated(cls, start_path: Path | None = None) -> builtins.list[DecoratedFunction]:
        """Find all codegen decorated functions in Python files under the given path.

        Args:
            start_path: Directory or file to start searching from. Defaults to current working directory.

        Returns:
            List of DecoratedFunction objects found in the files

        """
        if start_path is None:
            start_path = Path.cwd()

        # Look only in .codegen/codemods
        codemods_dir = start_path / ".codegen" / "codemods"
        if not codemods_dir.exists():
            return []

        all_functions = []
        seen_paths = set()  # Track unique file paths

        for path in codemods_dir.rglob("*.py"):
            # Skip if we've already processed this file
            if path in seen_paths:
                continue
            seen_paths.add(path)

            if _might_have_decorators(path):
                try:
                    functions = find_codegen_functions(path)
                    all_functions.extend(functions)
                except Exception:
                    pass  # Skip files we can't parse

        return all_functions
