import json

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


def get_function_context(function) -> dict:
    """Get the implementation, dependencies, and usages of a function."""
    context = {
        "implementation": {"source": function.source, "filepath": function.filepath},
        "dependencies": [],
        "usages": [],
    }

    # Add dependencies
    for dep in function.dependencies:
        # Hop through imports to find the root symbols source
        if isinstance(dep, Import):
            dep = hop_through_imports(dep)

        context["dependencies"].append({"source": dep.source, "filepath": dep.filepath})

    # Add usages
    for usage in function.usages:
        context["usages"].append(
            {
                "source": usage.usage_symbol.source,
                "filepath": usage.usage_symbol.filepath,
            }
        )

    return context


@codegen.function("generate-training-data")
def run(codebase: Codebase):
    """Generate training data using a node2vec-like approach for code embeddings.

    This codemod:
    1. Finds all functions in the codebase
    2. For each function:
       - Captures its implementation
       - Lists all dependencies (with their implementations)
       - Lists all usages (with their implementations)
    3. Outputs structured JSON data for training
    """
    # Track all function contexts
    training_data = {
        "functions": [],
        "metadata": {
            "total_functions": len(codebase.functions),
            "total_processed": 0,
            "avg_dependencies": 0,
            "avg_usages": 0,
        },
    }

    # Process each function in the codebase
    for function in codebase.functions:
        # Skip if function is too small
        if len(function.source.split("\n")) < 2:
            continue

        # Get function context
        context = get_function_context(function)

        # Only keep functions with enough context
        if len(context["dependencies"]) + len(context["usages"]) > 0:
            training_data["functions"].append(context)

    # Update metadata
    training_data["metadata"]["total_processed"] = len(training_data["functions"])
    if training_data["functions"]:
        training_data["metadata"]["avg_dependencies"] = sum(len(f["dependencies"]) for f in training_data["functions"]) / len(training_data["functions"])
        training_data["metadata"]["avg_usages"] = sum(len(f["usages"]) for f in training_data["functions"]) / len(training_data["functions"])

    # Print stats
    print(f"Processed {training_data['metadata']['total_processed']} functions")
    print(f"Average dependencies: {training_data['metadata']['avg_dependencies']:.2f}")
    print(f"Average usages: {training_data['metadata']['avg_usages']:.2f}")

    return training_data


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi", commit="887270ff8a54bb58c406b0651678a27589793d2f", language="python")

    print("Generating training data...")
    training_data = run(codebase)

    print("Saving training data...")
    with open("training_data.json", "w") as f:
        json.dump(training_data, f, indent=2)
    print("Training data saved to training_data.json")
