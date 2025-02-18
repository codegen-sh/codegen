from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_type_attributes_primitives(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
type Person = {
    name: string;
    age: number;
    email?: string;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        person_type = file.get_symbol("Person")
        assert person_type.attributes
        assert len(person_type.attributes) == 3


def test_type_attributes_no_attributes(tmpdir) -> None:
    FILE_NAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
type Person = {}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILE_NAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILE_NAME)
        person_type = file.get_symbol("Person")
        assert len(person_type.attributes) == 0
