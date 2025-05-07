from itertools import product

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.expressions.unpack import Unpack
from codegen.sdk.core.symbol_groups.dict import Dict
from codegen.sdk.typescript.function import TSFunction
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_dict_basic(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a: 1, b: 2, c: 3}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for child in symbol_dict:
            assert child
        assert symbol_dict["a"] == "1"
        assert symbol_dict["b"] == "2"
        assert symbol_dict["c"] == "3"
        del symbol_dict["c"]
        symbol_dict["d"] = "4"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a: 1, b: 2, d: 4}
"""
    )


def test_dict_multiline(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {
    a: 1,
    b: 2,
    c: 3,
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for child in symbol_dict:
            assert child
        assert symbol_dict["a"] == "1"
        assert symbol_dict["b"] == "2"
        assert symbol_dict["c"] == "3"
        del symbol_dict["c"]
        symbol_dict["d"] = "4"
        symbol_dict["e"] = "5"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {
    a: 1,
    b: 2,
    d: 4,
    e: 5,
}
"""
    )


def test_dict_insert(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a: 1, b: 2, c: 3}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["d"] = "4"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a: 1, b: 2, c: 3, d: 4}
"""
    )


cases = list(product(range(2), repeat=2))


@pytest.mark.parametrize("removes,inserts", cases, ids=[f"{removes=}-{inserts=}" for removes, inserts in cases])
def test_dict_interleaved(tmpdir, removes, inserts):
    ref_dict = {str(-1 + -i): -(i**2) for i in range(removes)}
    file = "test.ts"
    content = f"""
let symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(max(inserts, removes)):
            if i < inserts:
                ref_dict[str(i)] = i**2
                symbol_dict[str(i)] = i**2
            if i < removes:
                del ref_dict[str(-1 - i)]
                del symbol_dict[str(-1 - i)]
    assert (
        file.content
        == f"""
let symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("removes,inserts", cases, ids=[f"{removes=}-{inserts=}" for removes, inserts in cases])
def test_dict_removes_first(tmpdir, removes, inserts):
    ref_dict = {str(-1 + -i): -(i**2) for i in range(removes)}
    file = "test.ts"
    content = f"""
let symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(removes):
            del ref_dict[str(-1 - i)]
            del symbol_dict[str(-1 - i)]
        for i in range(inserts):
            ref_dict[str(i)] = i**2
            symbol_dict[str(i)] = i**2
    assert (
        file.content
        == f"""
let symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("removes,inserts", cases, ids=[f"{removes=}-{inserts=}" for removes, inserts in cases])
def test_dict_inserts_first(tmpdir, removes, inserts):
    ref_dict = {str(-1 + -i): -(i**2) for i in range(removes)}
    file = "test.ts"
    content = f"""
let symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(inserts):
            ref_dict[str(i)] = i**2
            symbol_dict[str(i)] = i**2
        for i in range(removes):
            del ref_dict[str(-1 - i)]
            del symbol_dict[str(-1 - i)]
    assert (
        file.content
        == f"""
let symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("existing,inserts", cases, ids=[f"{existing=}-{inserts=}" for existing, inserts in cases])
def test_dict_append_existing(tmpdir, existing, inserts):
    ref_dict = {str(-1 + -i): -(i**2) for i in range(existing)}
    file = "test.ts"
    content = f"""
let symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(inserts):
            ref_dict[str(i)] = i**2
            symbol_dict[str(i)] = i**2
    assert (
        file.content
        == f"""
let symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("existing", list(range(4)), ids=[f"existing={existing}" for existing in range(4)])
def test_dict_set_existing(tmpdir, existing):
    ref_dict = {str(-1 + -i): -(i**2) for i in range(existing)}
    file = "test.ts"
    content = f"""
let symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(existing):
            ref_dict[str(i)] = i**2
            symbol_dict[str(i)] = i**2
    assert (
        file.content
        == f"""
let symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("existing,inserts", cases, ids=[f"existing={existing + 1}-{inserts=}" for existing, inserts in cases])
def test_dict_set_existing_same(tmpdir, existing, inserts):
    ref_dict = {str(-1 + -i): -(i**2) for i in range(existing)}
    file = "test.ts"
    content = f"""
let symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(inserts):
            symbol_dict["1"] = i
            ref_dict["1"] = i
    assert (
        file.content
        == f"""
let symbol = {ref_dict}
"""
    )


def test_dict_empty(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        assert len(symbol_dict) == 0
        symbol_dict["a"] = 0
        symbol_dict["c"] = 1
        symbol_dict["e"] = "e"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a: 0, c: 1, e}
"""
    )


def test_dict_remove_insert(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a: 1}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["b"] = 1
        del symbol_dict["a"]
        symbol_dict["c"] = 2
    # language=typescript
    assert (
        file.content
        == """
let symbol = {b: 1, c: 2}
"""
    )


def test_dict_shorthand_remove_insert(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["b"] = "b"
        del symbol_dict["a"]
        symbol_dict["c"] = "c"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {b, c}
"""
    )


def test_dict_edit(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a: 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["a"] = 1
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a: 1}
"""
    )


def test_dict_edit_shorthand(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a: 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["a"] = "a"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a}
"""
    )


def test_dict_edit_not_shorthand(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["a"] = 1
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a: 1}
"""
    )


def test_dict_clear(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a: 1, b: 2, c, d}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict.clear()
    # language=typescript
    assert (
        file.content
        == """
let symbol = {}
"""
    )


@pytest.mark.xfail(reason="Not implemented Yet")
def test_dict_obj(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
function printCoord(pt: { x: number; y: number }) {
  console.log("The coordinate's x value is " + pt.x);
  console.log("The coordinate's y value is " + pt.y);
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol: TSFunction = file.get_symbol("printCoord")
        param: Dict = symbol.parameters[0].type
        param["z"] = "number"
    # language=typescript
    assert (
        file.content
        == """
function printCoord(pt: { x: number; y: number; z: number }) {
  console.log("The coordinate's x value is " + pt.x);
  console.log("The coordinate's y value is " + pt.y);
}
"""
    )


def test_dict_shorthand(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a, b, c}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for child in symbol_dict:
            assert child
        assert symbol_dict["a"] == "a"
        assert symbol_dict["b"] == "b"
        assert symbol_dict["c"] == "c"
        del symbol_dict["c"]
        symbol_dict["d"] = "d"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a, b, d}
"""
    )


def test_shorthand_multiline(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {
    a,
    b,
    c,
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for child in symbol_dict:
            assert child
        assert symbol_dict["a"] == "a"
        assert symbol_dict["b"] == "b"
        assert symbol_dict["c"] == "c"
        del symbol_dict["c"]
        symbol_dict["d"] = "d"
        symbol_dict["e"] = "e"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {
    a,
    b,
    d,
    e,
}
"""
    )


def test_convert_shorthand(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a: 1, b}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["a"] = "a"
        symbol_dict["b"] = "2"
        symbol_dict["c"] = "c"
        symbol_dict["d"] = "4"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a, b: 2, c, d: 4}
"""
    )


def test_dict_shorthand_insert(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
let symbol = {a: 1, b: 2, c: 3}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["d"] = "d"
    # language=typescript
    assert (
        file.content
        == """
let symbol = {a: 1, b: 2, c: 3, d}
"""
    )


def test_dict_function_values(tmpdir):
    # language=typescript
    content = """
export const mapper = {
    method1(param1: Type1, param2: Type2): ReturnType1 {
        return param1.value
    },

    method2({ arg1, arg2 }: InputType): ReturnType2 {
        if (!arg2) return { value: undefined }
        return {
            value: { ...arg2, count: arg2.count + 1 },
            modified: true
        }
    },

    method3({ id }: Type3): ReturnType3 {
        return { id: id, type: "test" }
    }
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        mapper = file.get_global_var("mapper")
        d = mapper.value
        assert isinstance(d, Dict)
        assert len(list(d.items())) == 3
        assert list(d.keys()) == ["method1", "method2", "method3"]
        assert all(isinstance(v, TSFunction) for v in list(d.values()))
        for key, func_def in d.items():
            func_def.insert_before("async ", newline=False, extended=False)
            func_def.set_return_type(f"Promise<{func_def.return_type.source}>")

    # language=typescript
    assert (
        file.content
        == """
export const mapper = {
    async method1(param1: Type1, param2: Type2): Promise<ReturnType1> {
        return param1.value
    },

    async method2({ arg1, arg2 }: InputType): Promise<ReturnType2> {
        if (!arg2) return { value: undefined }
        return {
            value: { ...arg2, count: arg2.count + 1 },
            modified: true
        }
    },

    async method3({ id }: Type3): Promise<ReturnType3> {
        return { id: id, type: "test" }
    }
}
"""
    )


def test_dict_usage(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
function foo() {}

let obj = {key: foo}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = file.get_function("foo")
        obj = file.get_symbol("obj")
        assert len(foo.symbol_usages) == 1
        assert {*foo.symbol_usages} == {obj}


def test_dict_usage_shorthand(tmpdir):
    file = "test.ts"
    # language=typescript
    content = """
function foo() {}

let obj = {foo}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = file.get_function("foo")
        obj = file.get_symbol("obj")
        assert len(foo.symbol_usages) == 1
        assert {*foo.symbol_usages} == {obj}


def test_dict_usage_spread(tmpdir):
    file = "test.ts"
    # language=typescript jsx
    # language=typescript
    content = """
function foo() {}

let obj = {1: "a", ...{a: foo()}}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = file.get_function("foo")
        obj = file.get_symbol("obj")
        assert len(foo.symbol_usages) == 1
        assert {*foo.symbol_usages} == {obj}
        dict = foo.usages[0].match.parent.parent
        assert isinstance(dict, Dict)
        unpack = dict.parent
        assert isinstance(unpack, Unpack)
        unpack.unwrap(dict)
    # language=typescript
    assert (
        file.content
        # language=typescript jsx
        == """
function foo() {}

let obj = {1: "a", a: foo()}
"""
    )


def test_dict_merge_basic(tmpdir) -> None:
    """Test basic merge functionality in TypeScript dictionaries."""
    file = "test.ts"
    # language=typescript
    content = """
const base1 = {x: 1, y: 2}
const base2 = {a: 3, ...base1}
const base3 = {c: 4, d: 5}
const result = {m: 0, ...base2, n: 5}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value

        # Should work - adding new keys
        result.merge("{p: 6, q: 7}")
        codebase.commit()
        assert (
            file.content
            == """
const base1 = {x: 1, y: 2}
const base2 = {a: 3, ...base1}
const base3 = {c: 4, d: 5}
const result = {m: 0, ...base2, n: 5, p: 6, q: 7}
"""
        )


def test_dict_merge_duplicate_keys(tmpdir) -> None:
    """Test merging with duplicate keys in TypeScript dictionaries."""
    file = "test.ts"
    # language=typescript
    content = """
const base1 = {x: 1, y: 2}
const base2 = {a: 3, ...base1}
const base3 = {c: 4, d: 5}
const result = {m: 0, ...base2, n: 5}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value

        # Should work - duplicate keys are allowed in TypeScript
        result.merge("{a: 9}")
        codebase.commit()
        assert (
            file.content
            == """
const base1 = {x: 1, y: 2}
const base2 = {a: 3, ...base1}
const base3 = {c: 4, d: 5}
const result = {m: 0, ...base2, n: 5, a: 9}
"""
        )


def test_dict_merge_multiple_unpacks(tmpdir) -> None:
    """Test merging multiple TypeScript dictionaries with unpacks."""
    file = "test.ts"
    # language=typescript
    content = """
const base1 = {x: 1, y: 2}
const base2 = {a: 3, ...base1}
const base3 = {c: 4, d: 5}
const result = {m: 0, ...base2, n: 5, p: 6, q: 7}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value

        # Should work - new unique keys and unpacks
        result.merge("{s: 10, ...base3}")
        codebase.commit()
        assert (
            file.content
            == """
const base1 = {x: 1, y: 2}
const base2 = {a: 3, ...base1}
const base3 = {c: 4, d: 5}
const result = {m: 0, ...base2, n: 5, p: 6, q: 7, s: 10, ...base3}
"""
        )


def test_dict_merge_objects(tmpdir) -> None:
    """Test merging TypeScript Dict objects directly."""
    file = "test.ts"
    # language=typescript
    content = """
const dict1 = {x: 1, y: 2}
const dict2 = {a: 3, ...dict1}
const dict3 = {b: 4, c: 5}
const dict4 = {d: 6, ...dict3}
const result = {m: 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value
        dict2 = file.get_symbol("dict2").value
        dict3 = file.get_symbol("dict3").value
        dict4 = file.get_symbol("dict4").value

        # Should work - merging multiple Dict objects
        result.merge(dict2, dict3)
        codebase.commit()
        assert (
            file.content
            == """
const dict1 = {x: 1, y: 2}
const dict2 = {a: 3, ...dict1}
const dict3 = {b: 4, c: 5}
const dict4 = {d: 6, ...dict3}
const result = {m: 0, a: 3, ...dict1, b: 4, c: 5}
"""
        )


def test_dict_unwrap_basic(tmpdir) -> None:
    """Test basic unwrapping of spread operators in TypeScript dictionaries."""
    file = "test.ts"
    # language=typescript
    content = """
const base = {x: 1, y: 2}
const dict1 = {a: 1, ...base, b: 2}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        dict1 = file.get_symbol("dict1").value
        assert len(dict1.unpacks) == 1
        dict1.unwrap()
        codebase.commit()
        assert (
            file.content
            == """
const base = {x: 1, y: 2}
const dict1 = {a: 1, b: 2, x: 1, y: 2}
"""
        )


def test_dict_unwrap_multiple_spreads(tmpdir) -> None:
    """Test unwrapping multiple spread operators in TypeScript dictionaries."""
    file = "test.ts"
    # language=typescript
    content = """
const base1 = {x: 1, y: 2}
const base2 = {z: 3, w: 4}
const dict1 = {a: 1, ...base1, b: 2, ...base2, c: 3}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        dict1 = file.get_symbol("dict1").value
        assert len(dict1.unpacks) == 2
        dict1.unwrap()
        codebase.commit()
        assert (
            file.content
            == """
const base1 = {x: 1, y: 2}
const base2 = {z: 3, w: 4}
const dict1 = {a: 1, b: 2, c: 3, x: 1, y: 2, z: 3, w: 4}
"""
        )


def test_dict_unwrap_nested_spreads(tmpdir) -> None:
    """Test unwrapping nested spread operators in TypeScript dictionaries."""
    file = "test.ts"
    # language=typescript
    content = """
const base1 = {x: 1, y: 2}
const base2 = {z: 3, ...base1}
const dict1 = {a: 1, ...base2, b: 2}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        dict1 = file.get_symbol("dict1").value
        assert len(dict1.unpacks) == 1
        dict1.unwrap()
        codebase.commit()
        assert (
            file.content
            == """
const base1 = {x: 1, y: 2}
const base2 = {z: 3, ...base1}
const dict1 = {a: 1, b: 2, z: 3, ...base1}
"""
        )


def test_dict_merge_variadic(tmpdir) -> None:
    """Test merging multiple dictionaries using variadic arguments."""
    file = "test.ts"
    content = """
const dict1 = {a: 1}
const dict2 = {b: 2}
const dict3 = {c: 3}
const result = {m: 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value
        dict2 = file.get_symbol("dict2").value
        dict3 = file.get_symbol("dict3").value

        # Test merging multiple Dict objects and strings
        result.merge(dict2, dict3, "{x: 4}", "{y: 5}")
        codebase.commit()
        assert (
            file.content
            == """
const dict1 = {a: 1}
const dict2 = {b: 2}
const dict3 = {c: 3}
const result = {m: 0, b: 2, c: 3, x: 4, y: 5}
"""
        )


def test_dict_merge_variadic_with_spreads(tmpdir) -> None:
    """Test merging multiple dictionaries with spreads using variadic arguments."""
    file = "test.ts"
    content = """
const base1 = {x: 1}
const base2 = {y: 2}
const dict1 = {a: 1, ...base1}
const dict2 = {b: 2, ...base2}
const result = {m: 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value
        dict1 = file.get_symbol("dict1").value
        dict2 = file.get_symbol("dict2").value

        # Test merging multiple Dict objects with spreads
        result.merge(dict1, dict2, "{z: 3}")
        codebase.commit()
        assert (
            file.content
            == """
const base1 = {x: 1}
const base2 = {y: 2}
const dict1 = {a: 1, ...base1}
const dict2 = {b: 2, ...base2}
const result = {m: 0, a: 1, ...base1, b: 2, ...base2, z: 3}
"""
        )


def test_dict_merge_variadic_duplicate_keys(tmpdir) -> None:
    """Test merging multiple dictionaries with duplicate keys using variadic arguments."""
    file = "test.ts"
    content = """
const dict1 = {a: 1, b: 2}
const dict2 = {c: 3, d: 4}
const result = {m: 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value
        dict1 = file.get_symbol("dict1").value
        dict2 = file.get_symbol("dict2").value

        # Test merging with duplicate keys - should work in TypeScript
        result.merge(dict1, dict2, "{a: 5}")  # Duplicate 'a' key is allowed
        codebase.commit()
        assert (
            file.content
            == """
const dict1 = {a: 1, b: 2}
const dict2 = {c: 3, d: 4}
const result = {m: 0, a: 1, b: 2, c: 3, d: 4, a: 5}
"""
        )


def test_dict_merge_variadic_duplicate_spreads(tmpdir) -> None:
    """Test merging multiple dictionaries with duplicate spreads using variadic arguments."""
    file = "test.ts"
    content = """
const base1 = {x: 1}
const dict1 = {...base1}
const dict2 = {y: 2}
const result = {m: 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value
        dict1 = file.get_symbol("dict1").value
        dict2 = file.get_symbol("dict2").value

        # Test merging with duplicate spreads - should work in TypeScript
        result.merge(dict1, dict2, "{...base1}")  # Duplicate spread is allowed
        codebase.commit()
        assert (
            file.content
            == """
const base1 = {x: 1}
const dict1 = {...base1}
const dict2 = {y: 2}
const result = {m: 0, ...base1, y: 2, ...base1}
"""
        )
