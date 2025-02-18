from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_py_import_is_dynamic_in_function(tmpdir):
    # language=python
    content = """
    def my_function():
        import foo  # Dynamic import inside function
        from bar import baz  # Another dynamic import

    import static_import  # Static import at module level
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        # Dynamic imports inside function
        assert imports[0].is_dynamic  # import foo
        assert imports[1].is_dynamic  # from bar import baz

        # Static import at module level
        assert not imports[2].is_dynamic  # import static_import


def test_py_import_is_dynamic_in_if_block(tmpdir):
    # language=python
    content = """
    import top_level  # Static import

    if condition:
        import conditional  # Dynamic import in if block
        from x import y    # Another dynamic import
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # top_level import
        assert imports[1].is_dynamic  # conditional import
        assert imports[2].is_dynamic  # from x import y


def test_py_import_is_dynamic_in_try_except(tmpdir):
    # language=python
    content = """
    import static_first  # Static import

    try:
        import dynamic_in_try  # Dynamic import in try block
        from x.y import z     # Another dynamic import
    except ImportError:
        pass
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_first import
        assert imports[1].is_dynamic  # dynamic_in_try import
        assert imports[2].is_dynamic  # from x.y import z


def test_py_import_is_dynamic_in_with_block(tmpdir):
    # language=python
    content = """
    import static_import  # Static import

    with context_manager():
        import dynamic_in_with  # Dynamic import in with block
        from a.b import c      # Another dynamic import
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_import
        assert imports[1].is_dynamic  # dynamic_in_with import
        assert imports[2].is_dynamic  # from a.b import c


def test_py_import_is_dynamic_in_class_method(tmpdir):
    # language=python
    content = """
    import static_import  # Static import

    class MyClass:
        def my_method(self):
            import dynamic_in_method  # Dynamic import in method
            from pkg import module    # Another dynamic import

        @classmethod
        def class_method(cls):
            import another_dynamic    # Dynamic import in classmethod
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_import
        assert imports[1].is_dynamic  # dynamic_in_method import
        assert imports[2].is_dynamic  # from pkg import module
        assert imports[3].is_dynamic  # another_dynamic import


def test_py_import_is_dynamic_in_nested_function(tmpdir):
    # language=python
    content = """
    import static_import  # Static import

    def outer_function():
        import dynamic_in_outer  # Dynamic import in outer function

        def inner_function():
            import dynamic_in_inner  # Dynamic import in inner function
            from x import y         # Another dynamic import
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_import
        assert imports[1].is_dynamic  # dynamic_in_outer import
        assert imports[2].is_dynamic  # dynamic_in_inner import
        assert imports[3].is_dynamic  # from x import y


def test_py_import_is_dynamic_in_else_clause(tmpdir):
    # language=python
    content = """
    import static_import  # Static import

    if condition:
        pass
    else:
        import dynamic_in_else  # Dynamic import in else clause
        from x import y        # Another dynamic import
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_import
        assert imports[1].is_dynamic  # dynamic_in_else import
        assert imports[2].is_dynamic  # from x import y


def test_py_import_is_dynamic_in_except_clause(tmpdir):
    # language=python
    content = """
    import static_import  # Static import

    try:
        pass
    except ImportError:
        import dynamic_in_except  # Dynamic import in except clause
        from x import y          # Another dynamic import
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_import
        assert imports[1].is_dynamic  # dynamic_in_except import
        assert imports[2].is_dynamic  # from x import y


def test_py_import_is_dynamic_in_finally_clause(tmpdir):
    # language=python
    content = """
    import static_import  # Static import

    try:
        pass
    except ImportError:
        pass
    finally:
        import dynamic_in_finally  # Dynamic import in finally clause
        from x import y          # Another dynamic import
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_import
        assert imports[1].is_dynamic  # dynamic_in_finally import
        assert imports[2].is_dynamic  # from x import y


def test_py_import_is_dynamic_in_while_statement(tmpdir):
    # language=python
    content = """
    import static_import  # Static import

    while condition:
        import dynamic_in_while  # Dynamic import in while loop
        from a import b         # Another dynamic import
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_import
        assert imports[1].is_dynamic  # dynamic_in_while import
        assert imports[2].is_dynamic  # from a import b


def test_py_import_is_dynamic_in_match_case(tmpdir):
    # language=python
    content = """
    import static_import  # Static import

    match value:
        case 1:
            import dynamic_in_case  # Dynamic import in case clause
            from x import y        # Another dynamic import
        case _:
            import another_dynamic  # Dynamic import in default case
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
        imports = file.imports

        assert not imports[0].is_dynamic  # static_import
        assert imports[1].is_dynamic  # dynamic_in_case import
        assert imports[2].is_dynamic  # from x import y
        assert imports[3].is_dynamic  # another_dynamic import
