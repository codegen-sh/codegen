from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_parse_simple_ternary_expression(tmpdir) -> None:
    # language=typescript
    content = """
const result = a + b ? a : b;
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        expression = file.symbols[0].value
        assert expression.condition.source == "a + b"
        assert expression.consequence.source == "a"
        assert expression.alternative.source == "b"


def test_parse_nested_ternary_expressions(tmpdir) -> None:
    # language=typescript
    content = """
const result = a ? (b ? c : d) : e;
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")
        top_expression = file.symbols[0].value

        nested_expression = top_expression.consequence.resolve()

        assert top_expression.condition.source == "a"
        assert top_expression.consequence.source == "(b ? c : d)"
        assert top_expression.alternative.source == "e"

        assert nested_expression.condition.source == "b"
        assert nested_expression.consequence.source == "c"
        assert nested_expression.alternative.source == "d"


def test_parse_complex_ternary_expression(tmpdir) -> None:
    # language=typescript
    content = """
const result = (a + b) ? a : (b ? c : d);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"dir/file1.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file: TSFile = codebase.get_file("dir/file1.ts")

        top_expression = file.symbols[0].value
        nested_expression = top_expression.alternative.resolve()

        assert top_expression.condition.source == "(a + b)"
        assert top_expression.consequence.source == "a"
        assert top_expression.alternative.source == "(b ? c : d)"

        assert nested_expression.condition.source == "b"
        assert nested_expression.consequence.source == "c"
        assert nested_expression.alternative.source == "d"
