from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_object_unpack(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
function foo() {
    const { a, b } = func();
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        foo = codebase.get_function("foo")
        assignments = foo.code_block.assignments
        assert len(assignments) == 2
        assert {assignment.name for assignment in assignments} == {"a", "b"}


def test_list_unpack(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
function foo() {
    const [ a, b ] = func();
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        foo = codebase.get_function("foo")
        assignments = foo.code_block.assignments
        assert len(assignments) == 2
        assert {assignment.name for assignment in assignments} == {"a", "b"}


def test_object_unpack_alias(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
function foo() {
    const { a, b: c } = func();
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        foo = codebase.get_function("foo")
        assignments = foo.code_block.assignments
        assert len(assignments) == 2
        assert {assignment.name for assignment in assignments} == {"a", "c"}
