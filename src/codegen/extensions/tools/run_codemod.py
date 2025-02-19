"""Tool for running custom codemod functions on the codebase."""

import difflib
import importlib.util
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from codegen import Codebase


def generate_diff(original: str, modified: str) -> str:
    """Generate a unified diff between two strings.

    Args:
        original: Original content
        modified: Modified content

    Returns:
        Unified diff as a string
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile="original",
        tofile="modified",
        lineterm="",
    )

    return "".join(diff)


def run_codemod(codebase: Codebase, codemod_source: str) -> dict[str, Any]:
    """Run a custom codemod function on the codebase.

    The codemod_source should define a function like:
    ```python
    def run(codebase: Codebase):
        # Make changes to the codebase
        ...
    ```

    Args:
        codebase: The codebase to operate on
        codemod_source: Source code of the codemod function

    Returns:
        Dict containing execution results and diffs

    Raises:
        ValueError: If codemod source is invalid or execution fails
    """
    # Get initial state of all files
    initial_states = {file.filepath: file.content for file in codebase.files if not getattr(file, "_binary", False) and not file.filepath.startswith(".codegen")}

    # Create a temporary module to run the codemod
    with NamedTemporaryFile(suffix=".py", mode="w", delete=False) as temp_file:
        # Add imports and write the codemod source
        temp_file.write("from codegen import Codebase\n\n")
        temp_file.write(codemod_source)
        temp_file.flush()

        try:
            # Import the temporary module
            spec = importlib.util.spec_from_file_location("codemod", temp_file.name)
            if not spec or not spec.loader:
                msg = "Failed to create module spec"
                raise ValueError(msg)

            module = importlib.util.module_from_spec(spec)
            sys.modules["codemod"] = module
            spec.loader.exec_module(module)

            # Verify run function exists
            if not hasattr(module, "run"):
                msg = "Codemod must define a 'run' function"
                raise ValueError(msg)

            # Run the codemod
            module.run(codebase)
            codebase.commit()

            # Get final state and compute diffs
            diffs = {}
            for filepath, initial_content in initial_states.items():
                file = codebase.get_file(filepath)
                if file and file.content != initial_content:
                    diffs[filepath] = generate_diff(initial_content, file.content)

            return {
                "status": "success",
                "diffs": diffs,
                "files_changed": len(diffs),
            }

        except Exception as e:
            msg = f"Codemod execution failed: {e!s}"
            raise ValueError(msg)

        finally:
            # Clean up temporary file
            Path(temp_file.name).unlink()
