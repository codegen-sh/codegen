import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


@pytest.mark.skip("No Autocommit")
def test_autocommit_move_rename(tmpdir) -> None:
    file1_name = "file1.ts"
    # language=typescript
    content1 = """
export function externalDep(): int {
    return 42;
}
"""
    file2_name = "file2.ts"
    # language=typescript
    content2 = """
import { externalDep } from "./file1";

function bar(): int {
    return externalDep() + 1;
}"""
    file3_name = "file3.ts"
    content3 = ""
    with get_codebase_session(tmpdir=tmpdir, files={file1_name: content1, file2_name: content2, file3_name: content3}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file(file1_name)
        file2 = codebase.get_file(file2_name)
        file3 = codebase.get_file(file3_name)
        external_dep = file1.get_function("externalDep")
        external_dep.rename("baz")
        bar = file2.get_function("bar")
        bar.rename("bar2")
        bar.move_to_file(file3, strategy="update_all_imports", include_dependencies=True)

    # language=typescript
    assert (
        file1.content
        == """
export function baz(): int {
    return 42;
}
"""
    )
    # language=typescript
    assert file2.content == """\nimport { baz } from "./file1";"""

    # language=typescript
    assert (
        file3.content
        == """import { baz } from 'file1';


export function bar2(): int {
    return baz() + 1;
}"""
    )
