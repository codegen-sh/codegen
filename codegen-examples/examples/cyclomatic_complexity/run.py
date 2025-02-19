import codegen
from codegen import Codebase
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement


@codegen.function("cyclomatic-complexity")
def run(codebase: Codebase):
    def calculate_cyclomatic_complexity(code_block):
        # Initialize cyclomatic complexity count
        complexity = 1  # Start with one for the default path

        # Count decision points
        for statement in code_block.statements:
            if isinstance(statement, IfBlockStatement):
                complexity += 1 + len(statement.elif_statements)  # +1 for if, each elif adds another path
                if statement.else_statement:
                    complexity += 1
            elif isinstance(statement, WhileStatement) or isinstance(statement, ForLoopStatement):
                complexity += 1  # Loops introduce a new path
            elif isinstance(statement, TryCatchStatement):
                complexity += 1  # try-catch introduces a new path
                # Count except blocks by counting nested code blocks after the first one (try block)
                complexity += len(statement.nested_code_blocks) - 1  # -1 to exclude the try block itself

        return complexity

    # Initialize total complexity
    total_complexity = 0
    # Count total functions
    total_functions = 0
    # Store results for sorting
    results = []

    # Get all functions or methods
    callables = codebase.functions + [m for c in codebase.classes for m in c.methods]

    # Analyze each function
    for function in callables:
        complexity = calculate_cyclomatic_complexity(function.code_block)
        results.append((function.name, complexity, function.filepath))
        total_complexity += complexity
        total_functions += 1

    # Sort by complexity (highest first)
    results.sort(key=lambda x: x[1], reverse=True)

    # Print summary
    print("\n📊 Cyclomatic Complexity Analysis")
    print("=" * 60)

    if total_functions > 0:
        average = total_complexity / total_functions
        print("\n📈 Overall Stats:")
        print(f"  • Total Functions: {total_functions}")
        print(f"  • Average Complexity: {average:.2f}")
        print(f"  • Total Complexity: {total_complexity}")

        print("\n🔍 Top 10 Most Complex Functions:")
        print("-" * 60)
        for name, complexity, filepath in results[:10]:
            # Truncate filepath if too long
            if len(filepath) > 40:
                filepath = "..." + filepath[-37:]
            print(f"  • {name:<30} {complexity:>3} | {filepath}")

        # Complexity distribution
        low = sum(1 for _, c, _ in results if c <= 5)
        medium = sum(1 for _, c, _ in results if 5 < c <= 10)
        high = sum(1 for _, c, _ in results if c > 10)

        print("\n📉 Complexity Distribution:")
        print(f"  • Low (1-5): {low} functions ({low / total_functions * 100:.1f}%)")
        print(f"  • Medium (6-10): {medium} functions ({medium / total_functions * 100:.1f}%)")
        print(f"  • High (>10): {high} functions ({high / total_functions * 100:.1f}%)")
    else:
        print("❌ No functions found in the codebase to analyze.")


if __name__ == "__main__":
    print("🔍 Analyzing codebase...")
    codebase = Codebase.from_repo("fastapi/fastapi", commit="887270ff8a54bb58c406b0651678a27589793d2f", language="python")

    print("Running analysis...")
    run(codebase)
