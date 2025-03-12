from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_parameter_remove(tmpdir) -> None:
    # language=python
    content = """
def foo(a, b, c):
    pass

def bar(x):
    return x
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        # Test remove a
        foo = file.get_function("foo")
        foo.get_parameter("a").remove()

    assert "def foo(b, c):" in file.source

    # Test remove c
    foo = file.get_function("foo")
    foo.get_parameter("c").remove()
    codebase.ctx.commit_transactions()
    assert "def foo(b):" in file.source

    # Test remove b
    foo = file.get_function("foo")
    foo.get_parameter("b").remove()
    codebase.ctx.commit_transactions()
    assert "def foo():" in file.source

    bar = file.get_function("bar")

    bar.parameters[0].remove()
    codebase.ctx.commit_transactions()
    assert "def bar():" in file.content


def test_parameter_remove_multiple(tmpdir) -> None:
    # language=python
    content = """
def foo(a, b, c):
    pass
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        # Test remove a, c, then b
        foo = file.get_function("foo")
        foo.get_parameter("a").remove()
        foo.get_parameter("c").remove()
        foo.get_parameter("b").remove()

        # Commit transactions

    assert "def foo():" in file.source


def test_parameter_remove_any_formatting(tmpdir) -> None:
    # language=python
    content1 = """
    def foo(a, b, c):
        return a + b + c

    def bar(x):
        return x
        """
    # language=python
    content2 = """
    from file1 import bar, foo

    def test():
        foo(1, 2, 3)
        foo(1,
            2, # some comment here
            3
        )
        bar("asdf")
        """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1, "file2.py": content2}) as codebase:
        file1 = codebase.get_file("file1.py")
        file2 = codebase.get_file("file2.py")
        foo = file1.get_function("foo")
        bar = file1.get_function("bar")

        foo.parameters[0].remove()

    foo = file1.get_function("foo")
    assert [p.name for p in foo.parameters] == ["b", "c"]
    assert all([len(call.args) == 2 for call in foo.call_sites])

    foo.parameters[1].remove()
    codebase.ctx.commit_transactions()

    foo = file1.get_function("foo")
    assert [p.name for p in foo.parameters] == ["b"]
    assert all([len(call.args) == 1 for call in foo.call_sites])

    bar = file1.get_function("bar")
    bar.parameters[0].remove()
    codebase.ctx.commit_transactions()

    bar = file1.get_function("bar")
    assert bar.parameters == []
    assert all([len(call.args) == 0 for call in bar.call_sites])
