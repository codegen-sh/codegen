from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_function_function_calls_gets_calls_in_return_statement(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
function notAnArrowFunc() {
    // Body
}

const arrowFunc = () => {
    // Body
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        function_symbol = codebase.get_symbol("arrowFunc")
        assert function_symbol.is_arrow
        assert "() => {" in function_symbol.source

        function_symbol = codebase.get_symbol("notAnArrowFunc")
        assert not function_symbol.is_arrow
        assert function_symbol._named_arrow_function is None


def test_function_arrow_to_named_use_current_name(tmpdir) -> None:
    # language=typescript
    content = """
// no parameter
let a = () => {
    return;
}

// single parameter without parentheses
var b = x => {
    return;
}

// multiple parameters with parentheses
const c = (x, y) => {
	return;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        file.get_function("a").arrow_to_named()
        file.get_function("b").arrow_to_named()
        file.get_function("c").arrow_to_named()

    # language=typescript
    assert (
        file.content
        == """
// no parameter
function a() {
    return;
}

// single parameter without parentheses
function b(x) {
    return;
}

// multiple parameters with parentheses
function c(x, y) {
	return;
}
    """
    )


def test_function_arrow_to_named_use_new_name(tmpdir) -> None:
    # language=typescript
    content = """
// no parameter
let a = () => {
    return;
}

// single parameter without parentheses
var b = x => {
    return;
}

// multiple parameters with parentheses
const c = (x, y) => {
	return;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        file.get_function("a").arrow_to_named("a_new")
        file.get_function("b").arrow_to_named("b_new")
        file.get_function("c").arrow_to_named("c_new")

    # language=typescript
    assert (
        file.content
        == """
// no parameter
function a_new() {
    return;
}

// single parameter without parentheses
function b_new(x) {
    return;
}

// multiple parameters with parentheses
function c_new(x, y) {
	return;
}
    """
    )


def test_function_arrow_to_named_preserves_async(tmpdir) -> None:
    # language=typescript
    content = """
// no parameter
let a = async () => {
    return;
}

// single parameter without parentheses
var b = async x => {
    return;
}

// multiple parameters with parentheses
const c = async (x, y) => {
    return;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        file.get_function("a").arrow_to_named()
        file.get_function("b").arrow_to_named()
        file.get_function("c").arrow_to_named()

    # language=typescript
    assert (
        file.content
        == """
// no parameter
async function a() {
    return;
}

// single parameter without parentheses
async function b(x) {
    return;
}

// multiple parameters with parentheses
async function c(x, y) {
    return;
}
    """
    )


def test_function_arrow_to_named_handles_body(tmpdir) -> None:
    # language=typescript
    content = """
export const a = () => someFunction(MyObject)
export const a = x => someFunction(MyObject)
export const a = () => { someFunction(MyObject) }
export const a = x => { someFunction(MyObject) }
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        for function in file.functions:
            function.arrow_to_named()

    # language=typescript
    assert (
        file.content
        == """
export function a() { return someFunction(MyObject) }
export function a(x) { return someFunction(MyObject) }
export function a() { someFunction(MyObject) }
export function a(x) { someFunction(MyObject) }
"""
    )


def test_function_arrow_to_named_keeps_return_type(tmpdir) -> None:
    # language=typescript
    content = """
const a = (): number => 1
const b = (x: number): number => x
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        for function in file.functions:
            function.arrow_to_named()

    # language=typescript
    assert (
        file.content
        == """
function a(): number { return 1 }
function b(x: number): number { return x }
    """
    )


def test_function_arrow_to_named_keeps_parameter_types(tmpdir) -> None:
    # language=typescript
    content = """
const a: MyObj<Props> = ({x, y}): MyType => 1;
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        file.get_function("a").arrow_to_named()

    # language=typescript
    assert (
        file.content
        == """
function a({x, y}: MyObj<Props>): MyType { return 1; }
    """
    )


def test_function_arrow_to_named_keeps_generic_types(tmpdir) -> None:
    # language=typescript
    content = """
const a = <T>() => 1;
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as codebase:
        file: TSFile = codebase.get_file("test.ts")
        file.get_function("a").arrow_to_named()

    # language=typescript
    assert (
        file.content
        == """
function a<T>() { return 1; }
    """
    )
