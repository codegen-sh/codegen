from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_destructured_parameters(tmpdir) -> None:
    filename = "test_arg.ts"
    # language=typescript
    file_content = """
export function GenericComponent({ param1, param2 }: Props) {
  const value = getValue()
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: file_content}) as codebase:
        file = codebase.get_file("test_arg.ts")
        symbol = file.get_function("GenericComponent")
        assert symbol is not None
        assert len(symbol.parameters) == 2
        assert symbol.parameters[0].name == "param1"
        assert symbol.parameters[0].is_destructured
        assert symbol.parameters[0].is_typed
        assert symbol.parameters[0].type == "Props"
        assert symbol.parameters[1].name == "param2"
        assert symbol.parameters[1].is_destructured
        assert symbol.parameters[1].is_typed
        assert symbol.parameters[1].type == "Props"


def test_get_type_from_destructured_parameters(tmpdir) -> None:
    filename = "test_arg.ts"
    # language=typescript
    file_content = """
type Props = {
  param1: Type1
  param2: Type2
}

export function GenericComponent({ param1, param2 }: Props) {
  const value = getValue()
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={filename: file_content}) as codebase:
        file = codebase.get_file("test_arg.ts")
        symbol = file.get_symbol("GenericComponent")
        assert symbol is not None
        assert len(symbol.parameters) == 2
        assert symbol.parameters[0].name == "param1"
        type = symbol.parameters[0].type.resolved_symbol
        assert type is not None
        assert type.__class__.__name__ == "TSTypeAlias"
        assert len(type.attributes) == 2
        assert type.attributes[0].name == "param1"
        assert type.attributes[1].name == "param2"
