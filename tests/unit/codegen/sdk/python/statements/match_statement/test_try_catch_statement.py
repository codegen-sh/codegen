from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement


def test_try_except_statement_parse(tmpdir) -> None:
    # language=python
    content = """
try:
    print(1/0)
except ZeroDivisionError as e:
    print(e)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        statements = file.code_block.statements
        try_except = statements[0]
        assert try_except.code_block.statements[0].source == "print(1/0)"
        except_clause = try_except.except_clauses[0]
        assert except_clause.condition == "ZeroDivisionError as e"
        assert except_clause.code_block.statements[0].source == "print(e)"


def test_try_except_statement_function_calls(tmpdir) -> None:
    # language=python
    content = """
try:
    risky_operation()
except SomeException as e:
    handle_exception()
    log_error(e)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        try_except = file.code_block.statements[0]
        function_calls = try_except.except_clauses[0].function_calls
        assert len(function_calls) == 2
        assert function_calls[0].source == "handle_exception()"
        assert function_calls[1].source == "log_error(e)"


def test_try_except_statement_dependencies(tmpdir) -> None:
    # language=python
    content = """
risky_var = 'risky'
def risky():
    try:
        print(risky_var)
    except NameError as e:
        print("Variable not defined:", e)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        risky_function = file.get_function("risky")
        dependencies = risky_function.dependencies
        assert len(dependencies) == 1
        assert dependencies[0] == file.get_global_var("risky_var")


def test_try_except_statement_is_wrapped_in(tmpdir) -> None:
    # language=python
    content = """
risky_var = 'risky'
def risky():
    call()
    try:
        call()
        if a:
            call()
    except NameError as e:
        pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        risky_function = file.get_function("risky")
        assert not file.function_calls[0].is_wrapped_in(TryCatchStatement)
        assert file.function_calls[1].is_wrapped_in(TryCatchStatement)
        assert file.function_calls[2].is_wrapped_in(TryCatchStatement)
