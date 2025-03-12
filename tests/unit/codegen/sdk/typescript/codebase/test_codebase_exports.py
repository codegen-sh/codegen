from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_codebase_exports(tmpdir) -> None:
    # language=typescript
    content = """
    export const a = 1;
    export let b = 2;
    export var c = 3;
    export function foo() {}
    export class Bar {}
    export interface IFoo {}
    export type MyType = string;
    export { foo as default };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        assert len(codebase.exports) == 8
        export_names = {exp.name for exp in codebase.exports}
        assert export_names == {"a", "b", "c", "foo", "Bar", "IFoo", "MyType", "default"}


def test_codebase_reexports(tmpdir) -> None:
    # language=typescript
    content1 = """
    export const x = 1;
    export const y = 2;
    """
    content2 = """
    export { x } from './file1';
    export { y as z } from './file1';
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        assert len(codebase.exports) == 4
        export_names = {exp.name for exp in codebase.exports}
        assert export_names == {"x", "y", "z"}


def test_codebase_default_exports(tmpdir) -> None:
    # language=typescript
    content = """
    const value = 42;
    export default value;
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        assert len(codebase.exports) == 1
        export = codebase.exports[0]
        assert export.name == "value"
