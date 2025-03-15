from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_for_loop_statement_parse(tmpdir) -> None:
    # language=python
    content = """
for i in range(10):
    print(i)
    print(i+1)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        statements = file.code_block.statements
        for_loop = statements[0]

        assert for_loop.item == "i"
        assert for_loop.iterable == "range(10)"
        assert len(for_loop.code_block.statements) == 2


def test_for_loop_statement_function_calls(tmpdir) -> None:
    # language=python
    content = """
for i in range(10 + foo()):
    init()
    if i % 2 == 0:
        increment()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        for_loop = file.code_block.statements[0]

        assert len(for_loop.function_calls) == 4
        assert for_loop.function_calls[0].source == "range(10 + foo())"
        assert for_loop.function_calls[1].source == "foo()"
        assert for_loop.function_calls[2].source == "init()"
        assert for_loop.function_calls[3].source == "increment()"


def test_for_loop_statement_dependencies(tmpdir) -> None:
    # language=python
    content = """
x = 0

def foo():
    for i in range(10):
        def a():
            x + i
            print(x)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")

        assert len(foo.dependencies) == 1
        assert foo.dependencies[0] == file.get_global_var("x")


def test_for_loop_statement_remove(tmpdir) -> None:
    # language=python
    content = """
x = 0

def foo():
    other()
    for i in range(10):
        func()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        file.function_calls[-1].remove()
    # language=python
    assert (
        file.content
        == """
x = 0

def foo():
    other()
    """
    )


def test_for_loop_statement_remove_pass(tmpdir) -> None:
    # language=python
    content = """
x = 0

def foo():
    for i in range(10):
        func()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        file.function_calls[-1].remove()
    # language=python
    assert (
        file.content
        == """
x = 0

def foo():
    pass
    """
    )


def test_for_loop_statement_remove_if_statement(tmpdir) -> None:
    # language=python
    content = """
x = 0

def foo():
    for i in range(10):
        if i:
            func()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        file.function_calls[-1].remove()
    # language=python
    assert (
        file.content
        == """
x = 0

def foo():
    for i in range(10):
        if i:
            pass
    """
    )
