from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions.boolean import Boolean
from codegen.sdk.core.expressions.number import Number
from codegen.sdk.core.expressions.string import String
from codegen.sdk.core.symbol_groups.dict import Dict
from codegen.sdk.core.symbol_groups.list import List
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_builtin_types(tmpdir):
    # language=typescript
    content = """
let a = 1;
let b = "hello";
let c = true;
let d = [1, 2, 3];
let e = {"a": 1, "b": 2};
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        # Test Number
        a = file.get_global_var("a")
        assert isinstance(a.value, Number)
        assert isinstance(a.value, int)

        # Test String
        b = file.get_global_var("b")
        assert isinstance(b.value, String)
        assert isinstance(b.value, str)

        # Test Boolean
        c = file.get_global_var("c")
        assert isinstance(c.value, Boolean)
        assert isinstance(c.value, bool)

        # Test List/Array
        d = file.get_global_var("d")
        assert isinstance(d.value, List)
        assert isinstance(d.value, list)

        # Test Dict/Object
        e = file.get_global_var("e")
        assert isinstance(e.value, Dict)
        assert isinstance(e.value, dict)
