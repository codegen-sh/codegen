import os
import shutil
import subprocess

import codegen
from codegen import Codebase
from codegen.sdk.core.detached_symbols.function_call import FunctionCall


def init_git_repo(repo_path: str) -> None:
    """Initialize a git repository in the given path."""
    subprocess.run(["git", "init"], cwd=repo_path, check=True)
    subprocess.run(["git", "add", "."], cwd=repo_path, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_path, check=True)


def cleanup_git_repo(repo_path: str) -> None:
    """Remove the .git directory from the given path."""
    git_dir = os.path.join(repo_path, ".git")
    if os.path.exists(git_dir):
        shutil.rmtree(git_dir)


@codegen.function("sqlalchemy-type-annotations")
def run(codebase: Codebase):
    """Add Mapped types to SQLAlchemy models in a codebase.

    This codemod:
    1. Finds all SQLAlchemy model classes
    2. Converts Column type annotations to Mapped types
    3. Adds necessary imports for the new type annotations
    """
    # Define type mapping
    column_type_to_mapped_type = {
        "Integer": "Mapped[int]",
        "Optional[Integer]": "Mapped[int | None]",
        "Boolean": "Mapped[bool]",
        "Optional[Boolean]": "Mapped[bool | None]",
        "DateTime": "Mapped[datetime | None]",
        "Optional[DateTime]": "Mapped[datetime | None]",
        "String": "Mapped[str]",
        "Optional[String]": "Mapped[str | None]",
        "Numeric": "Mapped[Decimal]",
        "Optional[Numeric]": "Mapped[Decimal | None]",
    }

    # Track statistics
    classes_modified = 0
    attributes_modified = 0

    # Traverse the codebase classes
    for cls in codebase.classes:
        class_modified = False
        original_source = cls.source  # Store original source before modifications

        for attribute in cls.attributes:
            if not attribute.assignment:
                continue

            assignment_value = attribute.assignment.value
            if not isinstance(assignment_value, FunctionCall):
                continue

            if assignment_value.name != "Column":
                continue

            db_column_call = assignment_value

            # Make sure we have at least one argument (the type)
            if len(db_column_call.args) == 0:
                continue

            # Check for nullable=True
            is_nullable = any(x.name == "nullable" and x.value == "True" for x in db_column_call.args)

            # Extract the first argument for the column type
            first_argument = db_column_call.args[0].source or ""
            first_argument = first_argument.split("(")[0].strip()

            # If the type is namespaced (e.g. sa.Integer), get the last part
            if "." in first_argument:
                first_argument = first_argument.split(".")[-1]

            # If nullable, wrap the type in Optional[...]
            if is_nullable:
                first_argument = f"Optional[{first_argument}]"

            # Check if we have a corresponding mapped type
            if first_argument not in column_type_to_mapped_type:
                print(f"Skipping unmapped type: {first_argument}")
                continue

            # Build the new mapped type annotation
            new_type = column_type_to_mapped_type[first_argument]

            # Update the assignment type annotation
            attribute.assignment.set_type_annotation(new_type)
            attributes_modified += 1
            class_modified = True

            # Add necessary imports
            if not cls.file.has_import("Mapped"):
                cls.file.add_import("from sqlalchemy.orm import Mapped\n")

            if "Optional" in new_type and not cls.file.has_import("Optional"):
                cls.file.add_import("from typing import Optional\n")

            if "Decimal" in new_type and not cls.file.has_import("Decimal"):
                cls.file.add_import("from decimal import Decimal\n")

            if "datetime" in new_type and not cls.file.has_import("datetime"):
                cls.file.add_import("from datetime import datetime\n")

        if class_modified:
            classes_modified += 1
            # Print the diff for this class
            print(f"\nModified class: {cls.name}")
            print("Before:")
            print(original_source)
            print("\nAfter:")
            print(cls.source)
            print("-" * 80)

    print("\nModification complete:")
    print(f"Classes modified: {classes_modified}")
    print(f"Attributes modified: {attributes_modified}")


if __name__ == "__main__":
    input_repo = "./input_repo"
    print("Initializing git repository...")
    init_git_repo(input_repo)

    print("Initializing codebase...")
    codebase = Codebase(input_repo)

    print("Running codemod...")
    run(codebase)

    print("Cleaning up git repository...")
    cleanup_git_repo(input_repo)
