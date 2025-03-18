from codegen.sdk.codebase.factory.get_session import get_codebase_session


def test_assignment_statement_remove(tmpdir) -> None:
    # language=python
    content = """
def foo():
    a = 1
    b = 2
    c = 3
    return a + b + c
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file("test.py")
        foo = file.get_function("foo")
        b = foo.code_block.get_local_var_assignment("b")
        b.remove()
        codebase.commit()

        assert file.content == "\ndef foo():\n    a = 1\n    c = 3\n    return a + b + c\n"
