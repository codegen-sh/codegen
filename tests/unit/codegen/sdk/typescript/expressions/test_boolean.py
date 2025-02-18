from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.boolean import Boolean
from codegen.sdk.typescript.assignment import TSAssignment
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_boolean_parse(tmpdir):
    # language=typescript
    content = """
const a = true;
const b = false;
const c = true;
const d = a || b || false || c;
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        a = file.get_global_var("a")
        b = file.get_global_var("b")
        d = file.get_global_var("d")

        assert a.value
        assert not b.value
        assert isinstance(a.value, Boolean)
        assert isinstance(b.value, Boolean)
        assert isinstance(d.value, BinaryExpression)
        # TODO: FIX THIS, should all resolve to Boolean types (CG-9489)
        assert [type(e.resolved_value) for e in d.value.elements] == [Boolean, TSAssignment, Boolean, Boolean]
