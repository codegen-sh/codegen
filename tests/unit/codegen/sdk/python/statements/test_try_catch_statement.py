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


def test_try_except_reassigment_handling(tmpdir) -> None:
    content = """
        try:
            PYSPARK = True # This gets removed even though there is a later use
        except ImportError:
            PYSPARK = False

        print(PYSPARK)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        symbo = file.get_symbol("PYSPARK")
        funct_call = file.function_calls[0]
        pyspark_arg = funct_call.args.children[0]
        for symb in file.symbols:
            usage = symb.usages[0]
            assert usage.match == pyspark_arg


def test_try_except_reassigment_handling_function(tmpdir) -> None:
    content = """
        try:
            def process():
                print('try')
        except ImportError:
            def process():
                print('except')
        finally:
            def process():
                print('finally')

        process()
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        process = file.get_function("process")
        funct_call = file.function_calls[3]  # Skip the print calls
        for idx, func in enumerate(file.functions):
            if idx == 2:
                usage = func.usages[0]
                assert usage.match == funct_call
            else:
                assert not func.usages


def test_try_except_reassigment_handling_inside_func(tmpdir) -> None:
    content = """
        def get_result():
            result = None
            try:
                result = "success"
            except Exception:
                result = "error"
            finally:
                result = "done"
            return result
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        get_result = file.get_function("get_result")
        return_stmt = get_result.code_block.statements[-1]
        result_var = return_stmt.value
        for idx, symb in enumerate(file.symbols(True)):
            if symb.name == "result":
                if idx == 4:
                    # The only usage is in the finally block
                    assert len(symb.usages) > 0
                    assert any(usage.match == result_var for usage in symb.usages)
                else:
                    assert len(symb.usages) == 0


def test_try_except_reassigment_handling_nested(tmpdir) -> None:
    content = """
        try:
            RESULT = "outer try"
            try:
                RESULT = "inner try"
            except Exception as e:
                RESULT = "inner except"
        except Exception as e:
            RESULT = "outer except"

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


def test_try_except_reassigment_with_finally(tmpdir) -> None:
    content = """
        try:
            STATUS = "trying"
        except Exception:
            STATUS = "error"
        finally:
            STATUS = "done"

        print(STATUS)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        funct_call = file.function_calls[0]
        status_arg = funct_call.args.children[0]
        for idx, symb in enumerate(file.symbols(True)):
            if symb.name == "STATUS":
                if idx == 2:
                    # The only usage is in the finally block
                    assert len(symb.usages) > 0
                    assert any(usage.match == status_arg for usage in symb.usages)
                else:
                    assert len(symb.usages) == 0


def test_try_except_reassigment_with_finally_nested(tmpdir) -> None:
    content = """
        try:
            STATUS = "trying"
        except Exception:
            STATUS = "error"
            try:
                STATUS = "trying"
            except Exception:
                STATUS = "error"
            finally:
                STATUS = "done"

        print(STATUS)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        funct_call = file.function_calls[0]
        status_arg = funct_call.args.children[0]
        for idx, symb in enumerate(file.symbols(True)):
            if symb.name == "STATUS":
                if idx == 0 or idx == 4:
                    # The only usage is in the finally block
                    assert len(symb.usages) > 0
                    assert any(usage.match == status_arg for usage in symb.usages)
                else:
                    assert len(symb.usages) == 0


def test_try_except_reassigment_with_finally_nested_deeper(tmpdir) -> None:
    content = """
        try:
            STATUS = "trying"
        except Exception:
            STATUS = "error"
            try:
                STATUS = "trying_lvl2"
            except Exception:
                STATUS = "error_lvl2"
            finally:
                try:
                    STATUS = "trying_lvl3"
                except Exception:
                    STATUS = "error_lvl3"
                finally:
                    STATUS = "done_lvl3"

        print(STATUS)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        funct_call = file.function_calls[0]
        status_arg = funct_call.args.children[0]
        for idx, symb in enumerate(file.symbols(True)):
            if symb.name == "STATUS":
                if idx == 0 or idx == 6:
                    # The only usage is in the finally block
                    assert len(symb.usages) > 0
                    assert any(usage.match == status_arg for usage in symb.usages)
                else:
                    assert len(symb.usages) == 0


def test_try_except_reassigment_with_finally_secondary_nested_deeper(tmpdir) -> None:
    content = """
        try:
            STATUS = "trying"
        except Exception:
            STATUS = "error"
            try:
                STATUS = "trying_lvl2"
            except Exception:
                STATUS = "error_lvl2"
            finally:
                try:
                    STATUS = "trying_lvl3"
                except Exception:
                    STATUS = "error_lvl3"

        print(STATUS)
    """

    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        funct_call = file.function_calls[0]
        status_arg = funct_call.args.children[0]
        for idx, symb in enumerate(file.symbols(True)):
            if symb.name == "STATUS":
                assert len(symb.usages) > 0
                assert any(usage.match == status_arg for usage in symb.usages)


def test_try_except_multiple_reassigment(tmpdir) -> None:
    content = """
        try:
            VALUE = "first try"
        except Exception:
            VALUE = "first except"

        try:
            VALUE = "second try"
        except Exception:
            VALUE = "second except"

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
