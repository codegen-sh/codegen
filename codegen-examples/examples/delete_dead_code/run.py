import codegen
from codegen import Codebase


@codegen.function("delete-dead-code")
def run(codebase: Codebase):
    removed_functions_count = 0
    removed_variables_count = 0

    for function in codebase.functions:
        # Skip test files
        if "test" in function.file.filepath:
            continue

        # Skip decorated functions
        if function.decorators:
            continue

        # Check if the function has no usages and no call sites
        if not function.usages and not function.call_sites:
            print(f"🗑️ Removing unused function: {function.name}")
            function.remove()
            removed_functions_count += 1

    # Clean up unused variables
    for func in codebase.functions:
        for var_assignments in func.code_block.local_var_assignments:
            if not var_assignments.local_usages:
                print(f"🧹 Removing unused variable: {var_assignments.name}")
                var_assignments.remove()
                removed_variables_count += 1

    print("\n")
    print(f"🔧 Total functions removed: {removed_functions_count}")
    print(f"📦 Total variables removed: {removed_variables_count}")


if __name__ == "__main__":
    print("🔍 Analyzing codebase...")
    codebase = Codebase.from_repo("tox-dev/tox", language="python", commit="b588b696e0940c1813014b31b68d7660d8a1914f")

    print("🚮 Deleting dead code...")
    run(codebase)
