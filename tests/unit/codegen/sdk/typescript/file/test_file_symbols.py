from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.class_definition import TSClass


def test_symbols_gets_class_symbol_with_correct_name(tmpdir) -> None:
    file = """
import  a from './utils.js';
import { b, c } from './utils/a.js';

class foo {
    bar() {
        return 42;
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 1
        assert set(s.name for s in symbols) == {"foo"}


def test_symbols_gets_class_with_constructor(tmpdir) -> None:
    file = """
class foo {
    constructor() {
        this.bar = 42;
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 1
        assert set(s.name for s in symbols) == {"foo"}


def test_symbols_gets_class_with_static_method(tmpdir) -> None:
    file = """
class foo {
    static bar() {
        return 42;
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 1
        assert set(s.name for s in symbols) == {"foo"}


def test_symbols_gets_class_with_getter_setter(tmpdir) -> None:
    file = """
class foo {
    get bar() {
        return this._bar;
    }

    set bar(value) {
        this._bar = value;
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 1
        assert set(s.name for s in symbols) == {"foo"}


def test_symbols_gets_class_with_inheritance(tmpdir) -> None:
    file = """
class bar {}

class foo extends bar {
    baz() {
        return 42;
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 2
        assert set(s.name for s in symbols) == {"foo", "bar"}


def test_symbols_gets_class_with_methods(tmpdir) -> None:
    file = """
class bar {}

class foo extends bar {
    baz() {
        return 42;
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")

        # =====[ symbols ]=====
        symbols = file.symbols
        assert len(symbols) == 2
        assert set(s.name for s in symbols) == {"foo", "bar"}

        # =====[ methods ]=====
        foo: TSClass = file.get_class("foo")
        assert foo is not None
        methods = foo.methods
        assert len(methods) == 1
        assert methods[0].name == "baz"

        # =====[ dependencies ]=====
        bar = file.get_class("bar")
        dependencies = foo.dependencies
        assert len(dependencies) == 1
        assert dependencies[0] == bar


def test_file_symbols_does_not_include_arrow_function(tmpdir) -> None:
    file = """
func("Do a function", () => {
      do_a_thing();
    })
  """
    # Should not get any functions
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert len(file.symbols) == 0


def test_file_symbols_includes_types(tmpdir) -> None:
    file = """
type Person = {
  name: string;
  age: number;
  email?: string;
};
type Dictionary<T> = {
  [key: string]: T;
};"""

    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        symbols = file.symbols
        assert len(symbols) == 2
        assert symbols[0].name == "Person"
        assert symbols[1].name == "Dictionary"
