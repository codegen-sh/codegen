from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions.boolean import Boolean
from codegen.sdk.core.expressions.comparison_expression import ComparisonExpression
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.core.statements.while_statement import WhileStatement


def test_while_statement_parse(tmpdir) -> None:
    # language=python
    content = """
# Single while statement
while True:
    print("Hello")
    break

# While statement with alternative
a = 1
b = 10
while a < b:
    a += 1
    print(a)
else:
    print("a is not less than b")
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        statements = file.code_block.statements
        simple_while = statements[1]
        while_else = statements[5]

        assert isinstance(simple_while, WhileStatement)
        assert isinstance(while_else, WhileStatement)
        assert simple_while.statement_type == StatementType.WHILE_STATEMENT
        assert while_else.statement_type == StatementType.WHILE_STATEMENT

        assert simple_while.condition == "True"
        assert isinstance(simple_while.condition, Boolean)
        assert len(simple_while.code_block.statements) == 2

        assert while_else.condition == "a < b"
        assert isinstance(while_else.condition, ComparisonExpression)
        assert len(while_else.code_block.statements) == 2
        assert isinstance(while_else.else_statement, IfBlockStatement)
        assert len(while_else.else_statement.consequence_block.statements) == 1


def test_while_statement_function_calls(tmpdir) -> None:
    # language=python
    content = """
a = 1

def foo():
    return a

def bar():
    return a + 1

c = 10

def test():
    while foo() + bar():
        print("Hello")
        if a > 10:
            print(c)
        break
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        test = file.get_function("test")
        while_statement = test.code_block.statements[0]

        test_calls = test.function_calls
        while_calls = while_statement.function_calls
        assert len(test_calls) == 4
        assert test_calls == while_calls


def test_while_statement_dependencies(tmpdir) -> None:
    # language=python
    content = """
a = 1

def foo():
    return a

def bar():
    return a + 1

c = 10

def test():
    print(c)
    while foo() + bar():
        print("Hello")
        break
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        test = file.get_function("test")

        test_dependencies = test.dependencies
        assert set([x.name for x in test_dependencies]) == {"foo", "bar", "c"}
        assert len(test_dependencies) == 3
