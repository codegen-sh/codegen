from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_functions_dependencies_async_function_finds_deps(tmpdir) -> None:
    ts_code = """
import {A} from './a'
const d = 123;

async function myFunction(a: A, b) {
  return a + b + d;
};
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ Test myFunction ]=====
        my_function = file.get_function("myFunction")
        assert my_function.name == "myFunction"
        my_function_deps = my_function.dependencies

        assert len(my_function_deps) == 2
        assert any(x.name == "A" for x in my_function_deps)
        assert any(x.name == "d" for x in my_function_deps)
        assert not any(x.name == "b" for x in my_function_deps)


def test_functions_dependencies_generator_function_finds_deps(tmpdir) -> None:
    ts_code = """
import {A} from './a'
const d = 123;

function* myFunction(a: A, b) {
  yield a + b + d;
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ Test myFunction ]=====
        my_function = file.get_function("myFunction")
        assert my_function.name == "myFunction"
        my_function_deps = my_function.dependencies

        assert len(my_function_deps) == 2
        assert any(x.name == "A" for x in my_function_deps)
        assert any(x.name == "d" for x in my_function_deps)
        assert not any(x.name == "b" for x in my_function_deps)


def test_functions_dependencies_arrow_function_finds_deps(tmpdir) -> None:
    ts_code = """
import {A} from './a'
const d = 123;

const myFunction = (a: A, b) => a + b + d;
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ Test myFunction ]=====
        my_function = file.get_function("myFunction")
        assert my_function.name == "myFunction"
        my_function_deps = my_function.dependencies

        assert len(my_function_deps) == 2
        assert any(x.name == "A" for x in my_function_deps)
        assert any(x.name == "d" for x in my_function_deps)
        assert not any(x.name == "b" for x in my_function_deps)


def test_functions_dependencies_function_expression_finds_deps(tmpdir) -> None:
    ts_code = """
import {A} from './a'
const d = 123;

const myFunction = function(a: A, b) {
  return a + b + d;
};
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ Test myFunction ]=====
        my_function = file.get_function("myFunction")
        assert my_function.name == "myFunction"
        my_function_deps = my_function.dependencies

        assert len(my_function_deps) == 2
        assert any(x.name == "A" for x in my_function_deps)
        assert any(x.name == "d" for x in my_function_deps)
        assert not any(x.name == "b" for x in my_function_deps)


def test_functions_dependencies_named_function_finds_deps(tmpdir) -> None:
    ts_code = """
import {A} from './a'
const d = 123;

function myFunction(a: A, b) {
  return a + b + d;
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ Test myFunction ]=====
        my_function = file.get_function("myFunction")
        assert my_function.name == "myFunction"
        my_function_deps = my_function.dependencies

        assert len(my_function_deps) == 2
        assert any(x.name == "A" for x in my_function_deps)
        assert any(x.name == "d" for x in my_function_deps)
        assert not any(x.name == "b" for x in my_function_deps)


def test_functions_dependencies_finds_function_dep(tmpdir) -> None:
    ts_code = """
function bar() {
    return 42;
}

export function foo() {
    bar();
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": ts_code}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ Test bar ]=====
        bar = file.get_function("bar")
        assert bar.name == "bar"

        # =====[ Test foo ]=====
        foo = file.get_function("foo")
        assert foo.name == "foo"
        assert len(foo.dependencies) == 1
        assert foo.dependencies[0] == bar


def test_function_dependencies_gets_param_type_annotations(tmpdir) -> None:
    file = """
import {A} from './a'
const d = 123;

function myFunc(args: {
    a: A,
    b: string,
    c: int,
}) {
    return d;
};

const equalsFunction = function(a: A, b) {
  return a + b + d;
};
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        my_func = file.get_function("myFunc")
        deps = my_func.dependencies
        assert len(deps) == 2
        assert any(x.name == "A" for x in deps)

        equals_function = file.get_function("equalsFunction")
        deps = equals_function.dependencies
        assert len(deps) == 2
        assert any(x.name == "A" for x in deps)
        assert not any(x.name == "b" for x in deps)
