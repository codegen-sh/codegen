import os
from pathlib import Path


def create_file(file_path: str, content: str | bytes) -> str:
    # Define the file path, name, and content
    filepath = os.path.dirname(file_path)
    filename = os.path.basename(file_path)
    content = content

    # Call the create_file function
    os.makedirs(filepath, exist_ok=True)

    # Create the full file path by joining the directory and filename
    file_path = os.path.join(filepath, filename)

    # Write the content to the file
    if isinstance(content, str):
        with open(file_path, "w") as file:
            file.write(content)
    elif isinstance(content, bytes):
        with open(file_path, "wb") as file:
            file.write(content)
    else:
        msg = f"Invalid content type: {type(content)}"
        raise ValueError(msg)

    # Check if the file was created
    file_path = os.path.join(filepath, filename)
    if not os.path.exists(file_path):
        msg = f"Failed to create file {format(file_path)}"
        raise FileNotFoundError(msg)
    return file_path


def create_files(base_dir: str, files: dict[str, str]) -> None:
    for filename, content in files.items():
        create_file(os.path.join(base_dir, filename), content)


def split_git_path(filepath: str) -> tuple[str, str | None]:
    """Split a filepath into (git_root, base_path) tuple by finding .git directory.

    Args:
        filepath (str): The full path to split

    Returns:
        tuple: (git_root_path, relative_path)

    Raises:
        ValueError: If the path is not in a git repository
    """
    # Convert to absolute path and resolve any symlinks
    path = Path(filepath).resolve()

    # Start from the given path and traverse up until we find .git
    current = path
    while current != current.parent:
        if (current / ".git").exists():
            # Found the git root
            git_root = str(current)
            rel_path = str(path.relative_to(current))

            # Handle the case where filepath is the git root itself
            if rel_path == ".":
                rel_path = None

            return (git_root, rel_path)
        current = current.parent

    # If we get here, we didn't find a .git directory
    msg = f"Path '{filepath}' is not in a git repository!"
    raise ValueError(msg)
