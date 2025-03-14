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


def test_match_reassigment_handling_function(tmpdir) -> None:
    content = """
action = "create"
match action:
    case "create":
        def process():
            print("creating")
    case "update":
        def process():
            print("updating")
    case _:
        def process():
            print("unknown action")

process()
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        process = file.get_function("process")
        funct_call = file.function_calls[3]  # Skip the print calls
        for func in file.functions:
            usage = func.usages[0]
            assert usage.match == funct_call


def test_match_reassigment_handling_inside_func(tmpdir) -> None:
    content = """
def get_message(status):
    result = None
    match status:
        case "success":
            result = "Operation successful"
        case "error":
            result = "An error occurred"
        case _:
            result = "Unknown status"
    return result
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        get_message = file.get_function("get_message")
        return_stmt = get_message.code_block.statements[-1]
        result_var = return_stmt.value
        for symb in file.symbols(True):
            if symb.name == "result":
                assert len(symb.usages) > 0
                assert any(usage.match == result_var for usage in symb.usages)


def test_match_reassigment_handling_nested(tmpdir) -> None:
    content = """
outer = "first"
match outer:
    case "first":
        RESULT = "outer first"
        inner = "second"
        match inner:
            case "second":
                RESULT = "inner second"
            case _:
                RESULT = "inner default"
    case _:
        RESULT = "outer default"

print(RESULT)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        funct_call = file.function_calls[0]
        result_arg = funct_call.args.children[0]
        for symb in file.symbols:
            if symb.name == "RESULT":
                usage = symb.usages[0]
                assert usage.match == result_arg


def test_match_multiple_reassigment(tmpdir) -> None:
    content = """
first = "a"
match first:
    case "a":
        VALUE = "first a"
    case _:
        VALUE = "first default"

second = "b"
match second:
    case "b":
        VALUE = "second b"
    case _:
        VALUE = "second default"

print(VALUE)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        funct_call = file.function_calls[0]
        value_arg = funct_call.args.children[0]
        for symb in file.symbols:
            if symb.name == "VALUE":
                usage = symb.usages[0]
                assert usage.match == value_arg


def test_match_complex_pattern_reassigment(tmpdir) -> None:
    content = """
data = {"type": "user", "name": "John", "age": 30}
match data:
    case {"type": "user", "name": name, "age": age} if age > 18:
        STATUS = "adult user"
    case {"type": "user", "name": name}:
        STATUS = "user with unknown age"
    case {"type": "admin"}:
        STATUS = "admin"
    case _:
        STATUS = "unknown"

print(STATUS)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        funct_call = file.function_calls[0]
        status_arg = funct_call.args.children[0]
        for symb in file.symbols:
            if symb.name == "STATUS":
                usage = symb.usages[0]
                assert usage.match == status_arg
