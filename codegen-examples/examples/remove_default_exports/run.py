import codegen
from codegen import Codebase
from codegen.sdk.typescript.file import TSFile


@codegen.function("remove-default-exports")
def run(codebase: Codebase):
    """Convert default exports to named exports in TypeScript files.

    This script:
    1. Identifies shared TypeScript files with default exports.
    2. Converts default exports to named exports.
    3. Ensures corresponding non-shared files are updated.
    """
    for file in codebase.files:
        target_file = file.filepath
        if not target_file:
            print(f"⚠️ Target file not found: {target_file} in codebase")
            continue

        # Get corresponding non-shared file
        non_shared_path = file.filepath.replace("/shared/", "/")
        if not codebase.has_file(non_shared_path):
            print(f"⚠️ No matching non-shared file for: {non_shared_path}")
            continue

        non_shared_file = codebase.get_file(non_shared_path)
        print(f"📄 Processing {file.filepath}")

        # Process individual exports
        if isinstance(file, TSFile):
            for export in file.exports:
                # Handle default exports
                if export.is_reexport() and export.is_default_export():
                    print(f"  🔄 Converting default export '{export.name}'")
                    default_export = next((e for e in non_shared_file.default_exports), None)
                    if default_export:
                        default_export.make_non_default()

            print(f"✨ Fixed exports in {file.filepath}")


if __name__ == "__main__":
    codebase = Codebase("./")
    run(codebase)
