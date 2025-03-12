from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_wrap_with_if_statement(tmpdir):
    # language=typescript jsx
    content = """
function funcA(a) {
    if (a) {
        print(a)
    }
    else {
        print(b)
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file1.tsx")
        function = file.get_function("funcA")
        function.code_block.wrap(before_src="if (undefined) {", after_src="}")
    # language=typescript jsx
    assert (
        file.content
        == """
function funcA(a) {
    if (undefined) {
        if (a) {
            print(a)
        }
        else {
            print(b)
        }
    }
}
    """
    )
