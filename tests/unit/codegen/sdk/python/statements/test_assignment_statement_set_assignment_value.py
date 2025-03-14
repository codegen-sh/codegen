from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_assignment_statement_set_assignment_value(tmpdir) -> None:
    # language=python
    content = """
def foo():
    a = 1
    b: int
    c = 3
    return a + b + c
"""
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        a = foo.code_block.get_local_var_assignment("a")
        a.set_value("2")
        b = foo.code_block.get_local_var_assignment("b")
        b.set_value("4")
        b.type.remove()
        c = foo.code_block.get_local_var_assignment("c")
        c.value.insert_after(" + a", newline=False)
        c.set_type_annotation("int")
        codebase.commit()

        assert (
            file.content
            == """
def foo():
    a = 2
    b = 4
    c: int = 3 + a
    return a + b + c
"""
        )


def test_assignment_statement_remove(tmpdir) -> None:
    # language=python
    content = """
def foo():
    a = 1
    b: int
    c = 3
    return a + b + c
"""
    # language=python
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        a = foo.code_block.get_local_var_assignment("a")
        a.set_type_annotation("int")
        a.value.remove()
        codebase.commit()

        assert (
            file.content
            == """
def foo():
    a: int
    b: int
    c = 3
    return a + b + c
"""
        )
