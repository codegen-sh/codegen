from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_code_block_all_statement_types(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
const GLOBAL_VAR = 1;

function sumEvenNumbers(numbers: number[], threshold: number = 11): number {
  /**
   * Calculates the sum of even numbers in an array.
   */
  // Variable declarations
  let sum: number;
  sum = 0;
  const isThresholdReached = (): boolean => sum > threshold;

  isThresholdReached();

  // For loop
  for (let i = 0; i < numbers.length; i++) {
    // Nested comment
    console.log(`Skipping odd number: ${num}`);
    if (i == 5) {
      return sum;
    }
  }

  // While loop
  while (sum < threshold) {
    sum++;
  }

  if (isThresholdReached()) {
    return sum;
  }
  return 0;
}
sumEvenNumbers([1, 2, 3, 4, 5]);
        """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        statements = file.get_function("sumEvenNumbers").code_block.get_statements()

        assert len(statements) == 18
        statement_types = [(x.index, x.statement_type, x.parent.level) for x in statements]
        assert statement_types == [
            (0, StatementType.COMMENT, 1),
            (1, StatementType.COMMENT, 1),
            (2, StatementType.ASSIGNMENT, 1),
            (3, StatementType.ASSIGNMENT, 1),
            (4, StatementType.SYMBOL_STATEMENT, 1),
            (5, StatementType.EXPRESSION_STATEMENT, 1),
            (6, StatementType.COMMENT, 1),
            (7, StatementType.FOR_LOOP_STATEMENT, 1),
            (0, StatementType.COMMENT, 2),
            (1, StatementType.EXPRESSION_STATEMENT, 2),
            (2, StatementType.IF_BLOCK_STATEMENT, 2),
            (0, StatementType.RETURN_STATEMENT, 3),
            (8, StatementType.COMMENT, 1),
            (9, StatementType.WHILE_STATEMENT, 1),
            (0, StatementType.EXPRESSION_STATEMENT, 2),
            (10, StatementType.IF_BLOCK_STATEMENT, 1),
            (0, StatementType.RETURN_STATEMENT, 2),
            (11, StatementType.RETURN_STATEMENT, 1),
        ]
