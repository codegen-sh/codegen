from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.sdk.core.expressions import String
from codegen.sdk.typescript.expressions.undefined_type import TSUndefinedType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_type_basic(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
function foo(a: string): number {
    let symbol = "test_string"
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = codebase.get_symbol("foo")
        assert foo.return_type.source == "number"
        assert foo.parameters[0].type == "string"
        foo.return_type.edit("string")
    # language=typescript
    assert (
        file.content
        == """
function foo(a: string): string {
    let symbol = "test_string"
}
"""
    )


def test_type_function(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
function foo(a: (a: number) => number): number {
    let symbol = "test_string"
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = codebase.get_symbol("foo")
        assert foo.parameters[0].type == "(a: number) => number"
        assert foo.parameters[0].type.return_type == "number"
        assert foo.parameters[0].type.parameters[0] == "a: number"
        foo.parameters[0].type.parameters.append("b: number")
    # language=typescript
    assert (
        file.content
        == """
function foo(a: (a: number, b: number) => number): number {
    let symbol = "test_string"
}
"""
    )


def test_type_object(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
function foo(a: {a: int; b?(a: int): c}): number {
    let symbol = "test_string"
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        foo = codebase.get_symbol("foo")
        assert foo.return_type.source == "number"
        a_type = foo.parameters[0].type
        assert a_type == "{a: int; b?(a: int): c}"
        assert a_type["a"] == "int"
        assert a_type["b"] == "b?(a: int): c"


def test_type_query(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
let n: typeof s;
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        n = codebase.get_symbol("n")
        assert n.type == "typeof s"
        assert n.is_typed
        assert n.type.query == "s"


def test_type_undefined(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
let n: undefined;
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        n = codebase.get_symbol("n")
        assert n.type == "undefined"
        assert isinstance(n.type, TSUndefinedType)


def test_type_readonly(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
let n: readonly T[];
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file(file)
        n = codebase.get_symbol("n")
        assert n.type.type == "T[]"


def test_type_multi_file(tmpdir) -> None:
    file = "test.ts"
    file2 = "test2.ts"
    # language=typescript
    content = """
import { foo } from "test2";

async function test_func(
    a: string,
): Promise<
    Other<
        x,
        foo["a"]["b"]["c"]
    >
>  {
}
"""
    # language=typescript
    content2 = """
export type foo = {
    [key: string]: {
        "bar": string
        "baz": string
        "bal": string
    }
};
"""
    with get_codebase_session(tmpdir=tmpdir, files={file: content, file2: content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        test_func = codebase.get_symbol("test_func")
        foo = codebase.get_symbol("foo")
        imp = codebase.get_file(file).imports[0]
        exp = foo.export
        override = test_func.return_type.parameters[0].parameters[1]
        assert len(foo.usages) == 3
        assert foo.symbol_usages == [test_func, exp, imp]
        assert len(foo.usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert override.resolved_symbol == foo
        assert len(foo.usages) == 3
        assert override.name == "foo"
        assert override.lookup == "c"
        assert override == 'foo["a"]["b"]["c"]'


def test_type_complex_generics(tmpdir) -> None:
    file = "test.ts"
    # language=typescript
    content = """
export async function exampleFunction<T>(
  payload: RequestPayload<T>,
  options?: RequestOptions
): Promise<
  WithOverride<
    schemas.ResponseType<T>,
    OperationsOverrides['example_operation']['response']
  >
> {
  return request({
    method: 'POST',
    path: '/v1/example',
    payload,
    headers: options?.headers,
    timeout: options?.timeout,
  })
}

"""
    # language=typescript
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        func = codebase.get_symbol("exampleFunction")
        ret = func.return_type
        assert ret.name == "Promise"
        assert (
            ret
            == """Promise<
  WithOverride<
    schemas.ResponseType<T>,
    OperationsOverrides['example_operation']['response']
  >
>"""
        )
        override = ret.parameters[0]
        assert override.name == "WithOverride"
        assert (
            override
            == """WithOverride<
    schemas.ResponseType<T>,
    OperationsOverrides['example_operation']['response']
  >"""
        )
        assert override.parameters[0] == "schemas.ResponseType<T>"
        assert override.parameters[1] == "OperationsOverrides['example_operation']['response']"
        assert override.parameters[1].name == "OperationsOverrides"
        assert override.parameters[1].lookup.ts_node_type == "string"
        assert isinstance(override.parameters[1].lookup, String)
        assert override.parameters[1].lookup == "response"
        assert override.parameters[1].type.lookup == "example_operation"
