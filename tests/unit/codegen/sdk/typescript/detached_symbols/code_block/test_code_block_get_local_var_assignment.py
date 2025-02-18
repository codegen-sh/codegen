from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_get_local_var_assignment_primitive(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function foo(x: number, y: string): MyClass {
    const z = String(x) + y;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        func = file.get_function("foo")

        z = func.code_block.get_local_var_assignment("z")
        assert z.name == "z"


def test_get_local_var_assignment_class_instance(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
class MyClass {
    attr1: string;
    attr2: string;
}

function foo(x: number, y: string): MyClass {
    const obj = new MyClass();
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        func = file.get_function("foo")

        obj = func.code_block.get_local_var_assignment("obj")
        assert obj.name == "obj"
