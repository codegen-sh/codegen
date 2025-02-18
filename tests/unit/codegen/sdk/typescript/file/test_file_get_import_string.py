from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_get_import_string_no_params(tmpdir) -> None:
    content = """
let age: number = 25;
let isStudent: boolean = true;
let scores: number[] = [90, 85, 92];
let person: { name: string, age: number } = { name: "Alice", age: 30 };
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")

        file_import_string = file.get_import_string()
        assert file_import_string == "import * as test from 'test'"
