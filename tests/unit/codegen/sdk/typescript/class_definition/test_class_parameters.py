from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_class_definition_parameters_gets_non_empty(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Person {
    constructor(name: string) {
        this.name = name;
    }
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={FILENAME: FILE_CONTENT.strip()},
    ) as codebase:
        file = codebase.get_file(FILENAME)
        person_class = file.get_symbol("Person")
        assert person_class.parameters
        assert len(person_class.parameters) == 1
        assert person_class.parameters[0].name == "name"
