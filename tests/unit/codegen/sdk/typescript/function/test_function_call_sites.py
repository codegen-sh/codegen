from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_call_sites_in_symbols(tmpdir) -> None:
    # language=typescript
    content = """
const globalVar = foo();

function foo(): void {
    a(1, 2);
    const b = c('3');
    return d(4);
}

class A {
    constructor() {
        foo();
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        foo = file.get_function("foo")

        assert len(foo.call_sites) == 2
        foo.rename("updatedFoo")
    # language=typescript
    assert (
        file.content
        == """
const globalVar = updatedFoo();

function updatedFoo(): void {
    a(1, 2);
    const b = c('3');
    return d(4);
}

class A {
    constructor() {
        updatedFoo();
    }
}
    """
    )


def test_function_call_sites_when_exported(tmpdir) -> None:
    # language=typescript
    content1 = """
export function foo(): void {
    a(1, 2);
    const b = c('3');
    return d(4);
}

foo();
"""
    # language=typescript
    content2 = """
import { foo as importedFunc } from './file1';

function bar(): void {
    importedFunc();
    someOtherFunction();
}
    """
    # language=typescript
    content3 = """
import * as myFile from './file1';

function myFunction(): void {
    myFile.foo();
    myFunction();
}
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file1.ts": content1, "file2.ts": content2, "file3.ts": content3},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")

        foo = file1.get_function("foo")
        assert len(foo.call_sites) == 3


def test_function_call_sites_in_file(tmpdir) -> None:
    # language=typescript
    content = """
foo()

function foo(): void {
    log('foo');
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        function_symbol = file.get_function("foo")

        assert len(function_symbol.call_sites) == 1
        function_symbol.rename("updatedFoo")
    # language=typescript
    assert (
        file.content
        == """
updatedFoo()

function updatedFoo(): void {
    log('foo');
}
"""
    )


def test_call_sites_finds_star_import_usage(tmpdir) -> None:
    # language=typescript
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "file1.ts": """export function foo(): void {}""",
            "file2.ts": """
import * as file1 from "./file1";

file1.foo();
""",
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")

        # =====[ Imports ]=====
        assert len(file2.imports) == 1
        imp = file2.imports[0]
        assert imp.from_file == file1

        # =====[ Function ]=====
        foo = file1.get_function("foo")
        assert foo.is_exported
        assert len(foo.call_sites) == 1
        call_site = foo.call_sites[0]
        assert call_site.file == file2


def test_call_sites_complex(tmpdir) -> None:
    # language=typescript
    content1 = """
export function foo<T = unknown>(
  param1: string,
  param2: Record<string, unknown> = {}
): Record<string, unknown> {
  return {
    value: param1
  }
}
    """

    # language=typescript
    content2 = """
import { foo } from './file1'

export function bar(param: string) {
  const { value } = foo<string>(param, {
    option1: true,
    option2: 'test'
  })
  return value
}
"""

    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "file1.ts": content1,
            "file2.ts": content2,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file2 = codebase.get_file("file2.ts")
        func = codebase.get_symbol("foo")
        assert len(func.call_sites) == 1
        func.call_sites[0].rename("foo2")
    # language=typescript
    assert (
        file2.content
        == """
import { foo } from './file1'

export function bar(param: string) {
  const { value } = foo2<string>(param, {
    option1: true,
    option2: 'test'
  })
  return value
}
"""
    )


def test_call_sites_double_invocation(tmpdir) -> None:
    # language=typescript
    content1 = """
function callback() {
    return () => {};
}

function foo() {}

function bar() {
    return callback(foo())();
}

function baz() {
    return (callback(foo())());
}
"""

    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "file1.ts": content1,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        func = codebase.get_symbol("foo")
        assert len(func.call_sites) == 2
        callback = codebase.get_symbol("callback")
        assert len(callback.call_sites) == 2


def test_call_sites_new_expression(tmpdir) -> None:
    # language=typescript
    content = """
class MyClass {
    constructor() {}
}

function foo() {
    const x = new MyClass();
    const y = new MyClass();
}

const z = new MyClass();
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        my_class = file.get_class("MyClass")
        assert len(my_class.call_sites) == 3
