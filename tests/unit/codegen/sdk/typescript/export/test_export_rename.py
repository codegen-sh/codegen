from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_rename_export_simple(tmpdir) -> None:
    # language=typescript
    content = """
import { b }  from "./b";
export default A =function() {b()};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        file.exports[0].rename("C")
    # language=typescript
    assert (
        file.content
        == """
import { b }  from "./b";
export default C =function() {b()};
    """
    )


def test_export_make_non_default(tmpdir) -> None:
    # language=typescript
    content = """
export default A = function() {b()};
export const B = 1;
    """
    # language=typescript
    content_alt = """
function foo() {}
export default foo;
    """
    # language=typescript
    content2 = """
import A from "./file";
console.log(A);
    """
    # language=typescript
    content3 = """
import A, { B } from "./file";
console.log(A, B);
    """
    # language=typescript
    content4 = """
export { default as A, B } from "./file";
    """
    # language=typescript
    content5 = """
export { default as renamed_A } from "./file";
    """
    # language=typescript
    content6 = """
import { A, B } from "./file4";
console.log(A, B);
    """
    # language=typescript
    content7 = """
export { default } from "./file";
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file.ts": content, "file_alt.ts": content_alt, "file2.ts": content2, "file3.ts": content3, "file4.ts": content4, "file5.ts": content5, "file6.ts": content6, "file7.ts": content7},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("file.ts")
        file_alt: TSFile = codebase.get_file("file_alt.ts")
        file2: TSFile = codebase.get_file("file2.ts")
        file3: TSFile = codebase.get_file("file3.ts")
        file4: TSFile = codebase.get_file("file4.ts")
        file5: TSFile = codebase.get_file("file5.ts")
        file6: TSFile = codebase.get_file("file6.ts")
        file7: TSFile = codebase.get_file("file7.ts")
        file.exports[0].make_non_default()
        file_alt.exports[0].make_non_default()
    # language=typescript
    assert (
        file.content
        == """
export const A = function() {b()};
export const B = 1;
    """
    )
    # language=typescript
    assert (
        file_alt.content
        == """
function foo() {}
export { foo };
    """
    )
    # language=typescript
    assert (
        file2.content
        == """
import { A } from "./file";
console.log(A);
    """
    )
    # language=typescript
    assert (
        file3.content
        == """
import { A, B } from "./file";
console.log(A, B);
    """
    )
    # language=typescript
    assert (
        file4.content
        == """
export { A, B } from "./file";
    """
    )
    # language=typescript
    assert (
        file5.content
        == """
export { A as renamed_A } from "./file";
    """
    )
    # language=typescript
    assert (
        file6.content
        == """
import { A, B } from "./file4";
console.log(A, B);
    """
    )
    # language=typescript
    assert (
        file7.content
        == """
export { A } from "./file";
    """
    )
