from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_match_switch_statement_parse(tmpdir) -> None:
    # language=python
    content = """
match 1/0:
    case ZeroDivisionError as e:
        print(e)
        print(1)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        statements = file.code_block.statements
        match_stmt = statements[0].cases[0]
        assert match_stmt.code_block.statements[0].source == "print(e)"
        assert match_stmt.code_block.statements[1].source == "print(1)"


def test_match_switch_statement_function_calls(tmpdir) -> None:
    # language=python
    content = """
match risky_operation():
    case SomeException as e:
        handle_exception()
        log_error(e)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        match_stmt = file.code_block.statements[0]
        case_clause = match_stmt.cases[0]
        statements = case_clause.code_block.statements
        assert len(statements) == 2
        assert statements[0].source == "handle_exception()"
        assert statements[1].source == "log_error(e)"


def test_match_switch_statement_dependencies(tmpdir) -> None:
    # language=python
    content = """
risky_var = 'risky'
def risky():
    match risky_var:
        case NameError as e:
            print("Variable not defined:", e)
        case _:
            print(risky_var)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        risky_function = file.get_function("risky")
        dependencies = risky_function.dependencies
        assert len(dependencies) == 1
        global_var = file.get_global_var("risky_var")
        assert dependencies[0] == global_var


def test_match_reassigment_handling(tmpdir) -> None:
    content = """
filter = 1
match filter:
    case 1:
        PYSPARK=True
    case 2:
        PYSPARK=False
    case _:
        PYSPARK=None

print(PYSPARK)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        symbo = file.get_symbol("PYSPARK")
        funct_call = file.function_calls[0]
        pyspark_arg = funct_call.args.children[0]
        for symb in file.symbols[1:]:
            usage = symb.usages[0]
            assert usage.match == pyspark_arg
