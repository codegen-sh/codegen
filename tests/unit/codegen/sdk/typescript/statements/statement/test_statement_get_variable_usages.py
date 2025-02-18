from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_if_statement_edit_variable_usages(tmpdir) -> None:
    """TODO(CG-8324): move to if_statement tests"""
    file_name = "test.ts"
    # language=typescript
    content = """
class MyClass {
    attr1: string;
    attr2: string;
    z: string;
}

function foo(x: number, y: string): MyClass {
    const z = String(x) + y;
    const obj = new MyClass();
    if (z === "some random string") {
        obj.attr1 = z;
    }
    for (let i = 0; i < 10; i++) {
        obj.attr2 += String(i);
    }
    while (obj.attr2 === "some random string" + z) {
        obj.z += z;
    }
    return obj;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        z = code_block.get_local_var_assignment("z")
        obj = code_block.get_local_var_assignment("obj")
        if_statement = code_block.statements[2]

        z_usages = if_statement.get_variable_usages(z.name)
        obj_usages = if_statement.get_variable_usages(obj.name)
        assert len(z_usages) == 2
        assert len(obj_usages) == 1
        z_usages[0].edit("new_z")
        z_usages[1].edit("new_z")
        obj_usages[0].edit("new_obj")
        all_z_usages = code_block.get_variable_usages(z.name)
        assert len(all_z_usages) == 4
    assert 'if (new_z === "some random string") {\n        new_obj.attr1 = new_z;' in file.content
