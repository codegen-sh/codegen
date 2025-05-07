from itertools import product
from typing import TYPE_CHECKING

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session

if TYPE_CHECKING:
    from codegen.sdk.core.symbol_groups.dict import Dict


def test_dict_basic(tmpdir) -> None:
    file = "test.py"
    # language=python
    content = """
symbol = {a: 1, b: 2, c: 3}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
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
    # language=python
    assert (
        file.content
        == """
symbol = {a: 1, b: 2, d: 4}
"""
    )


def test_dict_multiline(tmpdir) -> None:
    file = "test.py"
    # language=python
    content = """
symbol = {
    a: 1,
    b: 2,
    c: 3,
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
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
    # language=python
    assert (
        file.content
        == """
symbol = {
    a: 1,
    b: 2,
    d: 4,
    e: 5,
}
"""
    )


def test_dict_insert(tmpdir) -> None:
    file = "test.py"
    # language=python
    content = """
symbol = {a: 1, b: 2, c: 3}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["d"] = "4"
    # language=python
    assert (
        file.content
        == """
symbol = {a: 1, b: 2, c: 3, d: 4}
"""
    )


cases = list(product(range(2), repeat=2))


@pytest.mark.parametrize("removes,inserts", cases, ids=[f"{removes=}-{inserts=}" for removes, inserts in cases])
def test_dict_interleaved(tmpdir, removes, inserts) -> None:
    ref_dict = {-1 + -i: -(i**2) for i in range(removes)}
    file = "test.py"
    content = f"""
symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(max(inserts, removes)):
            if i < inserts:
                ref_dict[i] = i**2
                symbol_dict[i] = i**2
            if i < removes:
                del ref_dict[-1 - i]
                del symbol_dict[-1 - i]
    assert (
        file.content
        == f"""
symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("removes,inserts", cases, ids=[f"{removes=}-{inserts=}" for removes, inserts in cases])
def test_dict_removes_first(tmpdir, removes, inserts) -> None:
    ref_dict = {-1 + -i: -(i**2) for i in range(removes)}
    file = "test.py"
    content = f"""
symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(removes):
            del ref_dict[-1 - i]
            del symbol_dict[-1 - i]
        for i in range(inserts):
            ref_dict[i] = i**2
            symbol_dict[i] = i**2
    assert (
        file.content
        == f"""
symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("removes,inserts", cases, ids=[f"{removes=}-{inserts=}" for removes, inserts in cases])
def test_dict_inserts_first(tmpdir, removes, inserts) -> None:
    ref_dict = {-1 + -i: -(i**2) for i in range(removes)}
    file = "test.py"
    content = f"""
symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(inserts):
            ref_dict[i] = i**2
            symbol_dict[i] = i**2
        for i in range(removes):
            del ref_dict[-1 - i]
            del symbol_dict[-1 - i]
    assert (
        file.content
        == f"""
symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("existing,inserts", cases, ids=[f"{existing=}-{inserts=}" for existing, inserts in cases])
def test_dict_append_existing(tmpdir, existing, inserts) -> None:
    ref_dict = {-1 + -i: -(i**2) for i in range(existing)}
    file = "test.py"
    content = f"""
symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(inserts):
            ref_dict[i] = i**2
            symbol_dict[i] = i**2
    assert (
        file.content
        == f"""
symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("existing", list(range(4)), ids=[f"existing={existing}" for existing in range(4)])
def test_dict_set_existing(tmpdir, existing) -> None:
    ref_dict = {-1 + -i: -(i**2) for i in range(existing)}
    file = "test.py"
    content = f"""
symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(existing):
            ref_dict[i] = i**2
            symbol_dict[i] = i**2
    assert (
        file.content
        == f"""
symbol = {ref_dict}
"""
    )


@pytest.mark.parametrize("existing,inserts", cases, ids=[f"existing={existing + 1}-{inserts=}" for existing, inserts in cases])
def test_dict_set_existing_same(tmpdir, existing, inserts) -> None:
    ref_dict = {-1 + -i: -(i**2) for i in range(existing)}
    file = "test.py"
    content = f"""
symbol = {ref_dict}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        for i in range(inserts):
            symbol_dict[1] = i
            ref_dict[1] = i
    assert (
        file.content
        == f"""
symbol = {ref_dict}
"""
    )


def test_dict_empty(tmpdir) -> None:
    file = "test.py"
    # language=python
    content = """
symbol = {}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        assert len(symbol_dict) == 0
        symbol_dict["a"] = 0
        symbol_dict["c"] = 1
    # language=python
    assert (
        file.content
        == """
symbol = {a: 0, c: 1}
"""
    )


def test_dict_remove_insert(tmpdir) -> None:
    file = "test.py"
    # language=python
    content = """
symbol = {a: 1}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["b"] = 1
        del symbol_dict["a"]
        symbol_dict["c"] = 2
    # language=python
    assert (
        file.content
        == """
symbol = {b: 1, c: 2}
"""
    )


def test_dict_edit(tmpdir) -> None:
    file = "test.py"
    # language=python
    content = """
symbol = {a: 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict["a"] = 1
    # language=python
    assert (
        file.content
        == """
symbol = {a: 1}
"""
    )


def test_dict_clear(tmpdir) -> None:
    file = "test.py"
    # language=python
    content = """
symbol = {a: 1, b: 2, c: 3}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)

        symbol = file.get_symbol("symbol")
        symbol_dict: Dict = symbol.value
        symbol_dict.clear()
    # language=python
    assert (
        file.content
        == """
symbol = {}
"""
    )


def test_dict_merge(tmpdir) -> None:
    """Test merging dictionaries with and without spread operators."""
    file = "test.py"
    # language=python
    content = """
dict1 = {'a': 1, 'b': 2}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        dict1 = file.get_symbol("dict1").value
        dict1.merge("{'x': 3, 'y': 4}")
        codebase.commit()
        assert (
            file.content
            == """
dict1 = {'a': 1, 'b': 2, 'x': 3, 'y': 4}
"""
        )


def test_dict_unwrap(tmpdir) -> None:
    """Test unwrapping spread operators in dictionaries."""
    file = "test.py"
    # language=python
    content = """
base = {'x': 1, 'y': 2}
dict1 = {'a': 1, **base, 'b': 2}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        dict1 = file.get_symbol("dict1").value
        assert len(dict1.unpacks) == 1
        dict1.unwrap()
        codebase.commit()
        assert (
            file.content
            == """
base = {'x': 1, 'y': 2}
dict1 = {'a': 1, 'b': 2, 'x': 1, 'y': 2}
"""
        )


def test_dict_merge_variations(tmpdir) -> None:
    """Test various merge scenarios with different dictionary formats."""
    file = "test.py"
    # language=python
    content = """
simple = {'a': 1, 'b': 2}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        simple = file.get_symbol("simple").value
        simple.merge("{a: 1, b: 2}")
        codebase.commit()
        assert (
            file.content
            == """
simple = {'a': 1, 'b': 2, a: 1, b: 2}
"""
        )


def test_dict_unwrap_complex(tmpdir) -> None:
    """Test unwrapping in various complex scenarios."""
    file = "test.py"
    # language=python
    content = """
base1 = {'x': 1, 'y': 2}
dict1 = {**base1, 'z': 3}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        dict1 = file.get_symbol("dict1").value
        dict1.unwrap()
        codebase.commit()
        assert (
            file.content
            == """
base1 = {'x': 1, 'y': 2}
dict1 = {'z': 3, 'x': 1, 'y': 2}
"""
        )


def test_dict_merge_duplicate_unpack(tmpdir) -> None:
    """Test that merging with duplicate unpacks raises ValueError."""
    file = "test.py"
    # language=python
    content = """
base = {'x': 1, 'y': 2}
simple = {'m': 0, **base}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        simple = file.get_symbol("simple").value

        # Should raise ValueError because **base already exists in simple
        with pytest.raises(ValueError, match="Duplicate unpack found: \\*\\*base"):
            simple.merge("{'p': 6, **base}")
            codebase.commit()


def test_dict_merge_duplicate_keys(tmpdir) -> None:
    """Test that merging with duplicate keys raises ValueError."""
    file = "test.py"
    # language=python
    content = """
dict1 = {'a': 1, 'b': 2}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        dict1 = file.get_symbol("dict1").value

        # Should raise ValueError because 'a' already exists
        with pytest.raises(ValueError, match="Duplicate key found: 'a'"):
            dict1.merge("{'a': 3, 'c': 4}")
            codebase.commit()


def test_dict_merge_complex(tmpdir) -> None:
    """Test complex merge scenarios with multiple dictionaries and spreads."""
    file = "test.py"
    # language=python
    content = """
base1 = {'x': 1, 'y': 2}
base2 = {'a': 3, **base1}
base3 = {'c': 4, 'd': 5}
result = {'m': 0, **base2, 'n': 5}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value

        # Should work - no duplicate keys or unpacks
        result.merge("{'p': 6, 'q': 7}")
        codebase.commit()
        assert (
            file.content
            == """
base1 = {'x': 1, 'y': 2}
base2 = {'a': 3, **base1}
base3 = {'c': 4, 'd': 5}
result = {'m': 0, **base2, 'n': 5, 'p': 6, 'q': 7}
"""
        )

        # Should fail - trying to merge base1 when it's already unpacked via base2
        with pytest.raises(ValueError, match="Duplicate unpack found: \\*\\*base1"):
            result.merge("{'r': 8, **base1}")

        # Should fail - trying to add duplicate key 'a'
        with pytest.raises(ValueError, match="Duplicate key found: 'a'"):
            result.merge("{'a': 9}")


def test_dict_merge_multiple_unpacks(tmpdir) -> None:
    """Test merging multiple dictionaries with unpacks."""
    file = "test.py"
    # language=python
    content = """
base1 = {'x': 1, 'y': 2}
base2 = {'a': 3, **base1}
base3 = {'c': 4, 'd': 5}
result = {'m': 0, **base2, 'n': 5, 'p': 6, 'q': 7}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value

        # Should work - new unique keys and unpacks
        result.merge("{'s': 10, **base3}")
        codebase.commit()
        assert (
            file.content
            == """
base1 = {'x': 1, 'y': 2}
base2 = {'a': 3, **base1}
base3 = {'c': 4, 'd': 5}
result = {'m': 0, **base2, 'n': 5, 'p': 6, 'q': 7, 's': 10, **base3}
"""
        )


def test_dict_merge_objects(tmpdir) -> None:
    """Test merging Dict objects directly."""
    file = "test.py"
    # language=python
    content = """
dict1 = {'x': 1, 'y': 2}
dict2 = {'a': 3, **dict1}
dict3 = {'b': 4, 'c': 5}
dict4 = {'d': 6, **dict3}
result = {'m': 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
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
dict1 = {'x': 1, 'y': 2}
dict2 = {'a': 3, **dict1}
dict3 = {'b': 4, 'c': 5}
dict4 = {'d': 6, **dict3}
result = {'m': 0, 'a': 3, **dict1, 'b': 4, 'c': 5}
"""
        )


def test_dict_unpack_tracking(tmpdir) -> None:
    """Test tracking of unpacks in Python dictionaries."""
    file = "test.py"
    content = """
base1 = {'x': 1, 'y': 2}
base2 = {'z': 3, **base1}
dict1 = {'a': 1, **base2, 'b': 2}
dict2 = {'c': 3, **base1, **base2, 'd': 4}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)

        # Test simple unpack
        base2 = file.get_symbol("base2").value
        assert len(base2.unpacks) == 1
        assert base2.unpacks[0].source == "**base1"

        # Test single unpack with surrounding keys
        dict1 = file.get_symbol("dict1").value
        assert len(dict1.unpacks) == 1
        assert dict1.unpacks[0].source == "**base2"

        # Test multiple unpacks
        dict2 = file.get_symbol("dict2").value
        assert len(dict2.unpacks) == 2
        assert dict2.unpacks[0].source == "**base1"
        assert dict2.unpacks[1].source == "**base2"

        # Test that unpacks are preserved after merging
        dict2.merge("{'e': 5}")
        codebase.commit()
        assert len(dict2.unpacks) == 2
        assert (
            file.content
            == """
base1 = {'x': 1, 'y': 2}
base2 = {'z': 3, **base1}
dict1 = {'a': 1, **base2, 'b': 2}
dict2 = {'c': 3, **base1, **base2, 'd': 4, 'e': 5}
"""
        )


def test_dict_merge_variadic(tmpdir) -> None:
    """Test merging multiple dictionaries using variadic arguments."""
    file = "test.py"
    content = """
dict1 = {'a': 1}
dict2 = {'b': 2}
dict3 = {'c': 3}
result = {'m': 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value
        dict2 = file.get_symbol("dict2").value
        dict3 = file.get_symbol("dict3").value

        # Test merging multiple Dict objects and strings
        result.merge(dict2, dict3, "{'x': 4}", "{'y': 5}")
        codebase.commit()
        assert (
            file.content
            == """
dict1 = {'a': 1}
dict2 = {'b': 2}
dict3 = {'c': 3}
result = {'m': 0, 'b': 2, 'c': 3, 'x': 4, 'y': 5}
"""
        )


def test_dict_merge_variadic_with_unpacks(tmpdir) -> None:
    """Test merging multiple dictionaries with unpacks using variadic arguments."""
    file = "test.py"
    content = """
base1 = {'x': 1}
base2 = {'y': 2}
dict1 = {'a': 1, **base1}
dict2 = {'b': 2, **base2}
result = {'m': 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value
        dict1 = file.get_symbol("dict1").value
        dict2 = file.get_symbol("dict2").value

        # Test merging multiple Dict objects with unpacks
        result.merge(dict1, dict2, "{'z': 3}")
        codebase.commit()
        assert (
            file.content
            == """
base1 = {'x': 1}
base2 = {'y': 2}
dict1 = {'a': 1, **base1}
dict2 = {'b': 2, **base2}
result = {'m': 0, 'a': 1, **base1, 'b': 2, **base2, 'z': 3}
"""
        )


def test_dict_merge_variadic_duplicate_keys(tmpdir) -> None:
    """Test merging multiple dictionaries with duplicate keys using variadic arguments."""
    file = "test.py"
    content = """
dict1 = {'a': 1, 'b': 2}
dict2 = {'c': 3, 'd': 4}
result = {'m': 0}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.py": content}) as codebase:
        file = codebase.get_file(file)
        result = file.get_symbol("result").value
        dict1 = file.get_symbol("dict1").value
        dict2 = file.get_symbol("dict2").value

        # Should fail - trying to add duplicate key 'a'
        with pytest.raises(ValueError, match="Duplicate key found: 'a'"):
            result.merge(dict1, dict2, "{'a': 5}")
