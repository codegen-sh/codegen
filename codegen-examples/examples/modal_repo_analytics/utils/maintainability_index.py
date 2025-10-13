import codegen
from codegen import Codebase
import math
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.sdk.core.statements.while_statement import WhileStatement


# Halstead Volume functions
def get_operators_and_operands(function):
    operators = []
    operands = []

    for statement in function.code_block.statements:
        for call in statement.function_calls:
            operators.append(call.name)
            for arg in call.args:
                operands.append(arg.source)

        if hasattr(statement, "expressions"):
            for expr in statement.expressions:
                if isinstance(expr, BinaryExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])
                elif isinstance(expr, UnaryExpression):
                    operators.append(expr.ts_node.type)
                    operands.append(expr.argument.source)
                elif isinstance(expr, ComparisonExpression):
                    operators.extend([op.source for op in expr.operators])
                    operands.extend([elem.source for elem in expr.elements])

        if hasattr(statement, "expression"):
            expr = statement.expression
            if isinstance(expr, BinaryExpression):
                operators.extend([op.source for op in expr.operators])
                operands.extend([elem.source for elem in expr.elements])
            elif isinstance(expr, UnaryExpression):
                operators.append(expr.ts_node.type)
                operands.append(expr.argument.source)
            elif isinstance(expr, ComparisonExpression):
                operators.extend([op.source for op in expr.operators])
                operands.extend([elem.source for elem in expr.elements])

    return operators, operands


def calculate_halstead_volume(operators, operands):
    n1 = len(set(operators))
    n2 = len(set(operands))

    N1 = len(operators)
    N2 = len(operands)

    N = N1 + N2
    n = n1 + n2

    if n > 0:
        volume = N * math.log2(n)
        return volume, N1, N2, n1, n2
    return 0, N1, N2, n1, n2


# Cyclomatic Complexity functions
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

        if hasattr(statement, "condition") and hasattr(statement.condition, "source"):
            complexity += statement.condition.source.count(" and ") + statement.condition.source.count(" or ")

        if hasattr(statement, "nested_code_blocks"):
            for block in statement.nested_code_blocks:
                complexity += analyze_block(block)

        return complexity

    def analyze_block(block):
        if not block or not hasattr(block, "statements"):
            return 0
        return sum(analyze_statement(stmt) for stmt in block.statements)

    return 1 + analyze_block(function.code_block) if hasattr(function, "code_block") else 1


def calculate_maintainability_index(halstead_volume: float, cyclomatic_complexity: float, loc: int) -> float:
    """Calculate the normalized maintainability index for a given function.

    Args:
        halstead_volume: The Halstead volume metric
        cyclomatic_complexity: The cyclomatic complexity metric
        loc: Lines of code

    Returns:
        float: The maintainability index score normalized between 0 and 100
    """
    if loc <= 0:  # Prevents log(0)
        return 100

    try:
        # Calculate the raw maintainability index
        raw_mi = 171 - 5.2 * math.log(max(1, halstead_volume)) - 0.23 * cyclomatic_complexity - 16.2 * math.log(max(1, loc))

        # Normalize to 0-100 range
        normalized_mi = max(0, min(100, raw_mi * 100 / 171))
        return normalized_mi
    except (ValueError, TypeError):
        return 0


def get_maintainability_rank(mi_score: float) -> str:
    """Convert maintainability index score to a letter grade.

    Args:
        mi_score: The maintainability index score

    Returns:
        str: Letter grade from A to F
    """
    if mi_score >= 85:
        return "A"
    elif mi_score >= 65:
        return "B"
    elif mi_score >= 45:
        return "C"
    elif mi_score >= 25:
        return "D"
    else:
        return "F"


@codegen.function("maintainability-index")
def run(codebase: Codebase):
    results = []
    total_mi = 0
    total_functions = 0

    callables = codebase.functions + [m for c in codebase.classes for m in c.methods]

    for function in callables:
        if not hasattr(function, "code_block"):
            continue

        operators, operands = get_operators_and_operands(function)
        volume, N1, N2, n1, n2 = calculate_halstead_volume(operators, operands)
        complexity = calculate_cyclomatic_complexity(function)
        loc = len(function.code_block.source.splitlines())

        mi_score = calculate_maintainability_index(volume, complexity, loc)

        print(f"\n{function.name} ({function.filepath}):")
        print(f"  Maintainability Index: {mi_score:.2f}")
        print(f"  Cyclomatic Complexity: {complexity}")
        print(f"  Halstead Volume: {volume:.2f}")

        results.append(
            {
                "name": function.name,
                "filepath": function.filepath,
                "mi_score": mi_score,
                "rank": get_maintainability_rank(mi_score),
                "metrics": {"halstead_volume": volume, "cyclomatic_complexity": complexity, "loc": loc},
            }
        )

        total_mi += mi_score
        total_functions += 1

    results.sort(key=lambda x: x["mi_score"])

    # Print summary
    if total_functions > 0:
        avg_mi = total_mi / total_functions
        avg_cc = sum(r["metrics"]["cyclomatic_complexity"] for r in results) / total_functions
        avg_halstead = sum(r["metrics"]["halstead_volume"] for r in results) / total_functions

        print("\n📊 Maintainability Index Analysis")
        print("=" * 60)
        print("\n📈 Overall Stats:")
        print(f"  • Total Functions: {total_functions}")
        print(f"  • Average MI Score: {avg_mi:.2f} (Grade: {get_maintainability_rank(avg_mi)})")
        print(f"  • Average Cyclomatic Complexity: {avg_cc:.2f} (Grade: {cc_rank(avg_cc)})")
        print(f"  • Average Halstead Volume: {avg_halstead:.2f}")

        # Distribution analysis
        grades = {"A": 0, "B": 0, "C": 0, "D": 0, "F": 0}
        for result in results:
            grades[result["rank"]] += 1

        print("\n📉 Maintainability Distribution:")
        for grade, count in grades.items():
            percentage = (count / total_functions) * 100
            print(f"  • Grade {grade}: {count} functions ({percentage:.1f}%)")
    else:
        print("❌ No functions found in the codebase to analyze.")


if __name__ == "__main__":
    codebase = Codebase.from_repo("modal-labs/modal-client")
    run(codebase)
