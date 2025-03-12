from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_get_and_edit_variable_usages(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
class MyClass {
    attr1: string;
    attr2: string;
}

function foo(x: number, y: string): MyClass {
    const z = String(x) + y;
    const obj = new MyClass();
    obj.attr1 = z.obj;
    return obj;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        z = code_block.get_local_var_assignment("z")
        obj = code_block.get_local_var_assignment("obj")
        obj_name = obj.name
        obj_usage_statement = code_block.statements[2]
        assert obj_usage_statement.source == "obj.attr1 = z.obj;"

        z_usages = obj_usage_statement.get_variable_usages(z.name)
        assert len(z_usages) == 1
        assert z_usages[0].source == "z"
        z_usages[0].edit("renamed_attribute")

    assert "obj.attr1 = renamed_attribute.obj" in file.content
    code_block = file.get_function("foo").code_block
    obj_usage_statement = code_block.statements[2]
    obj_usages = obj_usage_statement.get_variable_usages(obj_name)
    assert len(obj_usages) == 1
    assert obj_usages[0].source == "obj"
    obj_usages[0].edit("renamed_obj")
    codebase.ctx.commit_transactions()
    assert "renamed_obj.attr1 = renamed_attribute.obj" in file.content


def test_unused_assignment_statement_var_has_no_usages(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
class MyClass {
    attr1: string;
    attr2: string;
}

function foo(x: number, y: string): MyClass {
    const z = String(x) + y;
    const obj = new MyClass();
    const random = "i'm an unused var!";
    obj.attr1 = z.obj;
    return obj;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block

        z = code_block.get_local_var_assignment("z")
        obj = code_block.get_local_var_assignment("obj")

        random = code_block.get_local_var_assignment("random")
        assert len(random.get_variable_usages(obj.name)) == 0
        assert len(random.get_variable_usages(z.name)) == 0
