from collections import Counter
from pathlib import Path
from typing import Literal

from codegen.shared.enums.programming_language import ProgrammingLanguage


def determine_project_language(folder_path: str, strategy: Literal["most_common", "package_json"] = "package_json") -> ProgrammingLanguage:
    """Determines the primary programming language of a project.

    Args:
        folder_path (str): Path to the folder to analyze
        strategy (Literal["most_common", "package_json"]): Strategy to use for determining language.
            "most_common" analyzes file extensions, "package_json" checks for package.json presence.

    Returns:
        ProgrammingLanguage: The determined programming language
    """
    # TODO: Create a new strategy that follows gitignore
    if strategy == "most_common":
        return _determine_language_by_file_count(folder_path)
    elif strategy == "package_json":
        return _determine_language_by_package_json(folder_path)


def _determine_language_by_package_json(folder_path: str) -> ProgrammingLanguage:
    """Determines project language by checking for presence of package.json.
    Faster but less accurate than file count strategy.

    Args:
        folder_path (str): Path to the folder to analyze

    Returns:
        ProgrammingLanguage: TYPESCRIPT if package.json exists, otherwise PYTHON
    """
    package_json_path = Path(folder_path) / "package.json"
    if package_json_path.exists():
        return ProgrammingLanguage.TYPESCRIPT
    else:
        return ProgrammingLanguage.PYTHON


def _determine_language_by_file_count(folder_path: str) -> ProgrammingLanguage:
    """Analyzes a folder to determine the primary programming language based on file extensions.
    Returns the language with the most matching files.

    Args:
        folder_path (str): Path to the folder to analyze

    Returns:
        ProgrammingLanguage: The dominant programming language, or UNSUPPORTED if no matching files found
    """
    from codegen.sdk.python import PyFile
    from codegen.sdk.typescript.file import TSFile

    EXTENSIONS = {
        ProgrammingLanguage.PYTHON: PyFile.get_extensions(),
        ProgrammingLanguage.TYPESCRIPT: TSFile.get_extensions(),
    }

    folder = Path(folder_path)
    if not folder.exists() or not folder.is_dir():
        msg = f"Invalid folder path: {folder_path}"
        raise ValueError(msg)

    # Initialize counters for each language
    language_counts = Counter()

    # Walk through the directory
    for file_path in folder.rglob("*"):
        # Skip directories and hidden files
        if file_path.is_dir() or file_path.name.startswith("."):
            continue

        # Skip common directories to ignore
        if any(ignore in str(file_path) for ignore in [".git", "node_modules", "__pycache__", "venv", ".env"]):
            continue

        # Count files for each language based on extensions
        for language, exts in EXTENSIONS.items():
            if file_path.suffix in exts:
                language_counts[language] += 1

    # If no files found, return None
    if not language_counts:
        return ProgrammingLanguage.UNSUPPORTED

    # Return the language with the highest count
    return language_counts.most_common(1)[0][0]
