import codegen
from codegen import Codebase
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement


def cc_rank(complexity):
    if complexity < 0:
        raise ValueError("Complexity must be a non-negative value")

    ranks = [(1, 5, "A"), (6, 10, "B"), (11, 20, "C"), (21, 30, "D"), (31, 40, "E"), (41, float("inf"), "F")]
    for low, high, rank in ranks:
        if low <= complexity <= high:
            return rank
    return "F"


def calculate_cyclomatic_complexity(function):
    def analyze_statement(statement):
        complexity = 0

        if isinstance(statement, IfBlockStatement):
            complexity += 1
            if hasattr(statement, "elif_statements"):
                complexity += len(statement.elif_statements)

        elif isinstance(statement, (ForLoopStatement, WhileStatement)):
            complexity += 1

        elif isinstance(statement, TryCatchStatement):
            complexity += len(getattr(statement, "except_blocks", []))

        if hasattr(statement, "condition") and isinstance(statement.condition, str):
            complexity += statement.condition.count(" and ") + statement.condition.count(" or ")

        if hasattr(statement, "nested_code_blocks"):
            for block in statement.nested_code_blocks:
                complexity += analyze_block(block)

        return complexity

    def analyze_block(block):
        if not block or not hasattr(block, "statements"):
            return 0
        return sum(analyze_statement(stmt) for stmt in block.statements)

    return 1 + analyze_block(function.code_block) if hasattr(function, "code_block") else 1


@codegen.function("cyclomatic-complexity")
def run(codebase: Codebase):
    results = []
    total_complexity = 0

    for function in codebase.functions:
        complexity = calculate_cyclomatic_complexity(function)
        rank = cc_rank(complexity)
        results.append({"name": function.name, "complexity": complexity, "rank": rank, "filepath": function.file.filepath})
        total_complexity += complexity

    results.sort(key=lambda x: x["complexity"], reverse=True)

    if results:
        print(f"Total Cyclomatic Complexity: {total_complexity}")
    else:
        print("❌ No functions found in the codebase to analyze.")


if __name__ == "__main__":
    codebase = Codebase.from_repo("modal-labs/modal-client")
    run(codebase)
