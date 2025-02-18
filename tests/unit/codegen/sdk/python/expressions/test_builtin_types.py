from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions.boolean import Boolean
from codegen.sdk.core.expressions.number import Number
from codegen.sdk.core.expressions.string import String
from codegen.sdk.core.symbol_groups.dict import Dict
from codegen.sdk.core.symbol_groups.list import List
from codegen.sdk.core.symbol_groups.tuple import Tuple
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_builtin_types(tmpdir):
    # language=python
    content = """
a = 1
b = "hello"
c = True
d = [1, 2, 3]
e = {"a": 1, "b": 2}
f = (1, 2, 3)
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}, programming_language=ProgrammingLanguage.PYTHON) as codebase:
        file = codebase.get_file("test.py")
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

        # Test List
        d = file.get_global_var("d")
        assert isinstance(d.value, List)
        assert isinstance(d.value, list)

        # Test Dict
        e = file.get_global_var("e")
        assert isinstance(e.value, Dict)
        assert isinstance(e.value, dict)

        # Test Tuple
        f = file.get_global_var("f")
        assert isinstance(f.value, Tuple)
        assert isinstance(f.value, tuple)
