import codegen
from codegen import Codebase
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.unary_expression import UnaryExpression
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
import math


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


@codegen.function("halstead-volume")
def run(codebase: Codebase):
    results = []
    total_volume = 0
    total_functions = 0

    callables = codebase.functions + [m for c in codebase.classes for m in c.methods]

    for function in callables:
        operators, operands = get_operators_and_operands(function)
        volume, N1, N2, n1, n2 = calculate_halstead_volume(operators, operands)

        results.append(
            {"name": function.name, "filepath": function.filepath, "volume": volume, "metrics": {"total_operators": N1, "total_operands": N2, "unique_operators": n1, "unique_operands": n2}}
        )

        total_volume += volume
        total_functions += 1

    # Print summary
    if total_functions > 0:
        print(f"Total Halstead Volume: {total_volume:.2f}")
    else:
        print("❌ No functions found in the codebase to analyze.")


if __name__ == "__main__":
    codebase = Codebase.from_repo("modal-labs/modal-client")
    run(codebase)
