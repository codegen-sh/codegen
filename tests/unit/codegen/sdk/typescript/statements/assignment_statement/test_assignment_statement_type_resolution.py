import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.typescript.expressions.object_type import TSObjectType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_assignment_statement_type_resolution_simple(tmpdir) -> None:
    # language=typescript
    content = """
const a: number = 0;
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        a = file.get_symbol("a")
        assert a.type == "number"


@pytest.mark.skip(reason="Not yet implemented CG-10064")
def test_assignment_statement_type_resolution_complex_unpack(tmpdir) -> None:
    # language=typescript
    content = """
const [a, b]: [number, string] = [1, 'test'];
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        a = file.functions[0].code_block.get_local_var_assignment("a")
        b = file.functions[0].code_block.get_local_var_assignment("b")
        assert a.name == "a"
        assert a.resolved_value == "number"
        assert b.resolved_value == "string"


@pytest.mark.skip(reason="Not yet implemented CG-10064")
def test_assignment_statement_type_resolution_nested_unpacking(tmpdir) -> None:
    # language=typescript
    content = """
const [[a, b], c]: [[number, string], boolean] = [[1, 'test'], true];
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        a = file.functions[0].code_block.get_local_var_assignment("a")
        b = file.functions[0].code_block.get_local_var_assignment("b")
        c = file.functions[0].code_block.get_local_var_assignment("c")
        assert a.name == "a"
        assert a.resolved_value == "number"
        assert b.resolved_value == "string"
        assert c.resolved_value == "boolean"


def test_simple_function_parameter_unpack(tmpdir) -> None:
    # language=typescript
    content = """
function simpleUnpack(args: { x: number; y: string }) {
    const { x, y } = args;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        x = file.functions[0].code_block.get_local_var_assignment("x")
        y = file.functions[0].code_block.get_local_var_assignment("y")
        assert x.name == "x"
        assert x.resolved_value == "number"
        assert y.name == "y"
        assert y.resolved_value == "string"


def test_nested_function_parameter_unpack(tmpdir) -> None:
    # language=typescript
    content = """
function nestedUnpack(args: { a: number; b: { c: string; d: boolean } }) {
    const { a, b: { c, d } } = args;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        a = file.functions[0].code_block.get_local_var_assignment("a")
        c = file.functions[0].code_block.get_local_var_assignment("c")
        d = file.functions[0].code_block.get_local_var_assignment("d")
        assert a.name == "a"
        assert a.resolved_value == "number"
        assert c.resolved_value == "string"
        assert d.resolved_value == "boolean"


def test_deeply_nested_function_parameter_unpack(tmpdir) -> None:
    # language=typescript
    content = """
function deeplyNestedUnpack(args: { a: number; b: { c: string; d: { e: boolean; f: string } } }) {
    const { a, b: { c, d: { e, f } } } = args;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        a = file.functions[0].code_block.get_local_var_assignment("a")
        c = file.functions[0].code_block.get_local_var_assignment("c")
        e = file.functions[0].code_block.get_local_var_assignment("e")
        f = file.functions[0].code_block.get_local_var_assignment("f")
        assert a.name == "a"
        assert a.resolved_value == "number"
        assert c.resolved_value == "string"
        assert e.resolved_value == "boolean"
        assert f.resolved_value == "string"


def test_complex_function_parameter_unpacking(tmpdir) -> None:
    # language=typescript
    content = """
async function processComplexArgs(args: {
    a: number;
    b: {
        c: string;
        d: {
            e: boolean;
            f: string;
        };
    };
}) {
    const {
        a,
        b: {
            c,
            d: {
                e,
                f
            }
        }
    } = args;
}
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file = codebase.get_file("test.ts")
        a = file.functions[0].code_block.get_local_var_assignment("a")
        b = file.functions[0].code_block.get_local_var_assignment("b")
        c = file.functions[0].code_block.get_local_var_assignment("c")
        e = file.functions[0].code_block.get_local_var_assignment("e")
        f = file.functions[0].code_block.get_local_var_assignment("f")
        assert a.name == "a"
        assert a.resolved_value == "number"
        assert c.resolved_value == "string"
        assert e.resolved_value == "boolean"
        assert f.resolved_value == "string"
        assert b.name == "b"
        assert isinstance(b.resolved_value, TSObjectType)
        assert list(b.resolved_value.keys()) == ["c", "d"]
