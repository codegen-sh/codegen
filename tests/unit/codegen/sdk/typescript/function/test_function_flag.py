from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_flag_with_message(tmpdir):
    # language=typescript
    content = """
function foo() {
    return;
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        foo = file.get_function("foo")

        foo.flag(message="This is a test")
        codebase.commit()

        expected = """
function foo() {
    return;
}  // 🚩 This is a test
"""
        assert file.content == expected
