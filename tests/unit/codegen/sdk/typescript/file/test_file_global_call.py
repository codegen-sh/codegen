from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_global_call(tmpdir) -> None:
    # language=typescript
    content = """
function foo(): void {
    // Empty function body
}

function bar(): void {
    foo();
}

foo();

if (true) {
    foo();
} else {
    foo();
}

Array.from({ length: 10 }, () => foo());
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_symbol("foo")
        assert len(foo.call_sites) == 5
