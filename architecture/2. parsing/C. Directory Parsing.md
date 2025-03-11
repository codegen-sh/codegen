# Directory Parsing

The Directory Parsing system is responsible for creating and maintaining a hierarchical representation of the codebase's directory structure in memory. Directories do not hold references to the file itself, but instead holds the names to the files and does a dynamic lookup when needed.

In addition to providing a more cohesive API for listing directory files, the Directory API is also used for [TSConfig](../3.%20imports-exports/C.%20TSConfig.md)-based (Import Resolution)[../3.%20imports-exports/A.%20Imports.md].

## Core Components

The Directory Tree is constructed during the initial build_graph step in codebase_context.py, and is recreated from scratch on every re-sync. More details are below:

## Directory Tree Construction

The directory tree is built through the following process:

1. The `build_directory_tree` method in `CodebaseContext` is called during graph initialization or when the codebase structure changes.
1. The method iterates through all files in the repository, creating directory objects for each directory path encountered.
1. For each file, it adds the file to its parent directory using the `_add_file` method.
1. Directories are created recursively as needed using the `get_directory` method with create_on_missing=True\`.

## Directory Representation

The `Directory` class provides a rich interface for working with directories:

- **Hierarchy Navigation**: Access parent directories and subdirectories
- **File Access**: Retrieve files by name or extension
- **Symbol Access**: Find symbols (classes, functions, etc.) within files in the directory
- **Directory Operations**: Rename, remove, or update directories

Each `Directory` instance maintains:

- A reference to its parent directory
- Lists of files and subdirectories
- Methods to recursively traverse the directory tree

## File Representation

Files are represented by the `File` class and its subclasses:

- `File`: Base class for all files, supporting basic operations like reading and writing content
- `SourceFile`: Specialized class for source code files that can be parsed into an AST

Files maintain references to:

- Their parent directory
- Their content (loaded dynamically to preserve the source of truth)
- For source files, the parsed AST and symbols

## Next Step

After the directory structure is parsed, the system can perform [Import Resolution](../3.%20imports-exports/A.%20Imports.md) to analyze module dependencies and resolve symbols across files.
