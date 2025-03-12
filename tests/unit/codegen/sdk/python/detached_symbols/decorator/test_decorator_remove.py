from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_decorator_remove(tmpdir) -> None:
    # language=python
    content = """
@decorator1
@decorator2
def foo():
    pass
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        # Test remove decorator1
        foo = file.get_function("foo")
        foo.decorators[0].remove()

    assert "@decorator1" not in file.source
    assert "@decorator2" in file.source

    # Test remove decorator2
    foo.decorators[0].remove()
    codebase.ctx.commit_transactions()
    assert "@decorator2" not in file.source


def test_decorator_remove_multiple(tmpdir) -> None:
    # language=python
    content = """
@decorator1
@decorator2
def foo():
    pass
    """

    with get_codebase_session(tmpdir=tmpdir, files={"file.py": content}) as codebase:
        file = codebase.get_file("file.py")

        # Test remove decorator1, then decorator2
        foo = file.get_function("foo")
        foo.decorators[0].remove()
        foo.decorators[-1].remove()

        # Commit transactions

    assert "@decorator1" not in file.source
    assert "@decorator2" not in file.source
