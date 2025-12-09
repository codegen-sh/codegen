import re

import codegen
from codegen import Codebase


@codegen.function("remove_empty_presenter_params")
def run(codebase: Codebase):
    """Find all usages of 'usePresenter' where the second argument is '{}' and remove that parameter.

    This script handles various forms of empty objects:
    - {}
    - { }
    - Object with whitespace
    """
    print("🔍 Searching for usePresenter calls with empty object as second parameter...")

    modified_files = 0
    modified_calls = 0

    # Regular expression to match empty objects with possible whitespace
    empty_obj_pattern = re.compile(r"^\s*{\s*}\s*$")

    # Iterate through all files in the codebase
    for file in codebase.files:
        file_modified = False

        # Look for function calls to usePresenter
        for call in file.function_calls:
            if call.name == "usePresenter" and len(call.arguments) >= 2:
                # Check if the second argument is an empty object {}
                second_arg = call.arguments[1]
                if empty_obj_pattern.match(second_arg.source_code):
                    print(f"🔧 Found usePresenter with empty object in {file.filepath}")
                    print(f"   Original: {call.source_code}")

                    # Remove the second argument
                    call.remove_argument(1)
                    file_modified = True
                    modified_calls += 1

                    print(f"   Modified: {call.source_code}")

        # Commit changes if the file was modified
        if file_modified:
            modified_files += 1

    # Commit all changes
    if modified_files > 0:
        codebase.commit()
        print(f"✅ Modified {modified_calls} usePresenter calls across {modified_files} files")
    else:
        print("ℹ️ No usePresenter calls with empty object parameters found")


if __name__ == "__main__":
    print("🚀 Starting script to remove empty usePresenter parameters...")

    # Initialize codebase with the appropriate language
    # You can change this to match your project's primary language
    codebase = Codebase("./", language="typescript")

    run(codebase)
    print("✅ Done! All empty usePresenter parameters have been removed!")
