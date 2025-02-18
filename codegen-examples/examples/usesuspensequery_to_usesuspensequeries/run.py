import codegen
from codegen import Codebase
from codegen.sdk.core.detached_symbols.function_call import FunctionCall


@codegen.function("useSuspenseQuery-to-useSuspenseQueries")
def run(codebase: Codebase):
    """Convert useSuspenseQuery calls to useSuspenseQueries in a React codebase.

    This codemod:
    1. Finds all files containing useSuspenseQuery
    2. Adds the necessary import statement
    3. Converts multiple useSuspenseQuery calls to a single useSuspenseQueries call
    """
    # Import statement for useSuspenseQueries
    import_str = "import { useQuery, useSuspenseQueries } from '@tanstack/react-query'"

    # Track statistics
    files_modified = 0
    functions_modified = 0

    # Iterate through all files in the codebase
    for file in codebase.files:
        if "useSuspenseQuery" not in file.source:
            continue

        print(f"Processing {file.filepath}")
        # Add the import statement
        file.add_import_from_import_string(import_str)
        file_modified = False

        # Iterate through all functions in the file
        for function in file.functions:
            if "useSuspenseQuery" not in function.source:
                continue

            results = []  # Store left-hand side of assignments
            queries = []  # Store query arguments
            old_statements = []  # Track statements to replace

            # Find useSuspenseQuery assignments
            for stmt in function.code_block.assignment_statements:
                if not isinstance(stmt.right, FunctionCall):
                    continue

                fcall = stmt.right
                if fcall.name != "useSuspenseQuery":
                    continue

                old_statements.append(stmt)
                results.append(stmt.left.source)
                queries.append(fcall.args[0].value.source)

            # Convert to useSuspenseQueries if needed
            if old_statements:
                new_query = f"const [{', '.join(results)}] = useSuspenseQueries({{queries: [{', '.join(queries)}]}})"
                print(f"Converting useSuspenseQuery to useSuspenseQueries in {function.name}")

                # Print the diff
                print("\nOriginal code:")
                print("\n".join(stmt.source for stmt in old_statements))
                print("\nNew code:")
                print(new_query)
                print("-" * 50)

                # Replace old statements with new query
                for stmt in old_statements:
                    stmt.edit(new_query)

                functions_modified += 1
                file_modified = True

        if file_modified:
            files_modified += 1

    print("\nModification complete:")
    print(f"Files modified: {files_modified}")
    print(f"Functions modified: {functions_modified}")
    codebase.commit()


if __name__ == "__main__":
    print("Initializing codebase...")
    codebase = Codebase.from_repo("deepfence/ThreatMapper", language="typescript")
    print("Running codemod...")
    run(codebase)
