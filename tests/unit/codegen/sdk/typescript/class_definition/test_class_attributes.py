from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_attributes_finds_correct_number(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Person {
  private name: string;
  private age: number;
  private email: string;
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        person = file.get_symbol("Person")
        assert len(person.attributes) == 3
        name_attribute = person.get_attribute("name")
        assert name_attribute.name == "name"
