from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_get_local_var_assignments_try_catch(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function foo(x: number, y: string): MyClass {
    try {
        const d = 1;
    } catch (e) {
        const f = 1;
    } finally {
        const g = 1;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        assert len(code_block.local_var_assignments) == 3
        assert [v.name for v in code_block.local_var_assignments] == ["d", "f", "g"]


def test_get_local_var_assignments_class_instance(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
class MyClass {
    attr1: string;
    attr2: string;
}

function foo(x: number, y: string): MyClass {
    var obj = new MyClass();
    return obj;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        assert len(code_block.local_var_assignments) == 1
        assert [v.name for v in code_block.local_var_assignments] == ["obj"]


def test_get_local_var_assignments_top_level(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function foo(x: number, y: string): MyClass {
    const z = String(x) + y;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        assert len(code_block.local_var_assignments) == 1
        assert [v.name for v in code_block.local_var_assignments] == ["z"]


def test_get_local_var_assignments_while_loop(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function foo(x: number, y: string) {
    while (obj.attr2 === "some random string" + z) {
        const c = 3;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        assert len(code_block.local_var_assignments) == 1
        assert [v.name for v in code_block.local_var_assignments] == ["c"]


def test_get_local_var_assignments_if_block(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function foo(x: number, y: string) {
    if (true) {
        let a = 1;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        assert len(code_block.local_var_assignments) == 1
        assert [v.name for v in code_block.local_var_assignments] == ["a"]


def test_get_local_var_assignments_for_loop(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function foo(x: number, y: string) {
    for (let i = 0; i < 10; i++) {
        const b = 2;
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        assert len(code_block.local_var_assignments) == 1
        assert [v.name for v in code_block.local_var_assignments] == ["b"]
