from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_assignment_statement_type_annotation_returns_none_if_missing(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function foo(width: number, height: number): number {
  const area = width * height;
  return area;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block
        area_assignment = code_block.get_local_var_assignment("area")
        assert area_assignment
        assert not area_assignment.type


def test_assignment_statement_type_annotation_returns_statement_if_exists(tmpdir) -> None:
    file_name = "test.ts"
    # language=typescript
    content = """
function foo(width: number, height: number): number {
  const area: number = width * height;
  return area;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={file_name: content}) as codebase:
        file = codebase.get_file(file_name)
        code_block = file.get_function("foo").code_block
        area_assignment = code_block.get_local_var_assignment("area")
        assert area_assignment
        assert area_assignment.type
        assert area_assignment.type.source == "number"
        area_assignment.remove()
    # language=typescript
    assert (
        file.content.strip()
        == """
function foo(width: number, height: number): number {
  return area;
}""".strip()
    )
