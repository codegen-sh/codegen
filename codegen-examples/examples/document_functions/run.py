import codegen
from codegen import Codebase
from codegen.sdk.core.external_module import ExternalModule
from codegen.sdk.core.import_resolution import Import
from codegen.sdk.core.symbol import Symbol


def hop_through_imports(imp: Import) -> Symbol | ExternalModule:
    """Finds the root symbol for an import"""
    if isinstance(imp.imported_symbol, Import):
        return hop_through_imports(imp.imported_symbol)
    return imp.imported_symbol


def get_extended_context(symbol: Symbol, degree: int) -> tuple[set[Symbol], set[Symbol]]:
    """Recursively collect dependencies and usages up to the specified degree.

    Args:
        symbol: The symbol to collect context for
        degree: How many levels deep to collect dependencies and usages

    Returns:
        A tuple of (dependencies, usages) where each is a set of related Symbol objects
    """
    dependencies = set()
    usages = set()

    if degree > 0:
        # Collect direct dependencies
        for dep in symbol.dependencies:
            # Hop through imports to find the root symbol
            if isinstance(dep, Import):
                dep = hop_through_imports(dep)

            if isinstance(dep, Symbol) and dep not in dependencies:
                dependencies.add(dep)
                dep_deps, dep_usages = get_extended_context(dep, degree - 1)
                dependencies.update(dep_deps)
                usages.update(dep_usages)

        # Collect usages in the current symbol
        for usage in symbol.usages:
            usage_symbol = usage.usage_symbol
            # Hop through imports for usage symbols too
            if isinstance(usage_symbol, Import):
                usage_symbol = hop_through_imports(usage_symbol)

            if isinstance(usage_symbol, Symbol) and usage_symbol not in usages:
                usages.add(usage_symbol)
                usage_deps, usage_usages = get_extended_context(usage_symbol, degree - 1)
                dependencies.update(usage_deps)
                usages.update(usage_usages)

    return dependencies, usages


@codegen.function("document-functions")
def run(codebase: Codebase):
    # Define the maximum degree of dependencies and usages to consider for context
    N_DEGREE = 2

    # Filter out test and tutorial functions first
    functions = [f for f in codebase.functions if not any(pattern in f.name.lower() for pattern in ["test", "tutorial"]) and not any(pattern in f.filepath.lower() for pattern in ["test", "tutorial"])]

    # Track progress for user feedback
    total_functions = len(functions)
    processed = 0

    print(f"Found {total_functions} functions to process (excluding tests and tutorials)")

    for function in functions:
        processed += 1

        # Skip if already has docstring
        if function.docstring:
            print(f"[{processed}/{total_functions}] Skipping {function.name} - already has docstring")
            continue

        print(f"[{processed}/{total_functions}] Generating docstring for {function.name} at {function.filepath}")

        # Collect context using N-degree dependencies and usages
        dependencies, usages = get_extended_context(function, N_DEGREE)

        # Generate a docstring using the AI with the context
        docstring = codebase.ai(
            """
            Generate a docstring for this function using the provided context.
            The context includes:
            - dependencies: other symbols this function depends on
            - usages: other symbols that use this function
        """,
            target=function,
            # `codebase.ai` is smart about stringifying symbols
            context={"dependencies": list(dependencies), "usages": list(usages)},
        )

        # Set the generated docstring for the function
        if docstring:
            function.set_docstring(docstring)
            print("  ✓ Generated docstring")
        else:
            print("  ✗ Failed to generate docstring")

        # Commit after each function so work is saved incrementally
        # This allows for:
        # 1. Safe early termination - progress won't be lost
        # 2. Immediate feedback - can check results while running
        # 3. Smaller atomic changes - easier to review/revert if needed
        codebase.commit()

    print(f"\nCompleted processing {total_functions} functions")


if __name__ == "__main__":
    print("Parsing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi", commit="887270ff8a54bb58c406b0651678a27589793d2f")

    print("Running function...")
    run(codebase)
