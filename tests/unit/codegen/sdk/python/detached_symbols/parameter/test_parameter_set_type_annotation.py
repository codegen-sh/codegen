from codegen.sdk.codebase.factory.get_session import get_codebase_session

DEFAULT_FILE_NAME = "test_for_one_test.py"


def test_parameter_set_type_annotation(tmpdir) -> None:
    # language=python
    content1 = """
def foo(x, y=1):
    return x

def bar(y: int):
    return y

def baz(x: int, y: str, z: list[int]) -> str:
    return str(x) + y + z[0]
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.py": content1}) as codebase:
        file1 = codebase.get_file("file1.py")

        # =====[ Trivial case ]=====
        foo = file1.get_function("foo")
        param = foo.parameters[0]
        param.set_type_annotation("int")
        param = foo.parameters[1]
        param.set_type_annotation("int")
    foo = file1.get_function("foo")
    param = foo.parameters[0]
    assert param.type == "int"
    param = foo.parameters[1]
    assert param.type == "int"
    # TODO: should autofix spacing?
    assert "def foo(x: int, y: int=1):" in foo.source

    # =====[ Already has a parameter ]=====
    bar = file1.get_function("bar")
    param = bar.parameters[0]
    param.set_type_annotation("str")
    codebase.ctx.commit_transactions()
    bar = file1.get_function("bar")
    param = bar.parameters[0]
    assert param.type == "str"
    assert "def bar(y: str):" in bar.source

    # =====[ Multiple parameters - replace middle one ]=====
    baz = file1.get_function("baz")
    param = baz.parameters[1]
    param.set_type_annotation("int")
    codebase.ctx.commit_transactions()
    baz = file1.get_function("baz")
    param = baz.parameters[1]
    assert param.type == "int"
    assert "def baz(x: int, y: int, z: list[int]) -> str:" in baz.source
