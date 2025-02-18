from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_get_and_edit_variable_usages(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function bar(x: number, y: number, z: number): number {
    return x + y + z;
}

function foo(x: number, y: string): MyClass {
    const z = String(x) + y;
    const obj = new MyClass();
    obj.attr1 = bar({x: 3, y: parseInt(y), z: Number(z)});
    if (true) {
        const a = 1;
    }
    for (let i = 0; i < 10; i++) {
        const b = 2;
    }
    while (obj.attr2 === "some random string" + z) {
        const c = 3;
    }
    return obj;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        func = file.get_function("foo")
        code_block = func.code_block

        x_usages = code_block.get_variable_usages("x")
        y_usages = code_block.get_variable_usages("y")
        z_usages = code_block.get_variable_usages("z")
        assert len(x_usages) == 1
        assert len(y_usages) == 2
        assert len(z_usages) == 2

        for x_usage in x_usages:
            x_usage.edit("new_x")
        for y_usage in y_usages:
            y_usage.edit("new_y")
        code_block.get_local_var_assignment("z").rename("new_z")

    # language=typescript
    expected_content = """
function bar(x: number, y: number, z: number): number {
    return x + y + z;
}

function foo(x: number, y: string): MyClass {
    const new_z = String(new_x) + new_y;
    const obj = new MyClass();
    obj.attr1 = bar({x: 3, y: parseInt(new_y), z: Number(new_z)});
    if (true) {
        const a = 1;
    }
    for (let i = 0; i < 10; i++) {
        const b = 2;
    }
    while (obj.attr2 === "some random string" + new_z) {
        const c = 3;
    }
    return obj;
}
    """
    assert file.content == expected_content
