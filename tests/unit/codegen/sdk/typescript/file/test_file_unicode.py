from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_unicode_move_symbol(tmpdir) -> None:
    # language=typescript
    content1 = """
export function externalDep(): string {
    return "🎇" + 42;
}
"""
    # language=typescript
    content2 = """
import { externalDep } from "./file1";

function foo(): string {
    return fooDep() + 1 + "🐍";
}

function fooDep(): string {
    return 24 + "🐲";
}

export function bar(): string {
    return externalDep() + barDep() + "🔗";
}

function barDep(): string {
    return "😀";
}
"""
    # language=typescript
    content3 = """
import { bar } from "./file2";

function baz(): string {
    return bar() + "🤯" + 1;
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

        bar = file2.get_function("bar")
        bar.move_to_file(file3, include_dependencies=True, strategy="add_back_edge")

    assert file1.content == content1
    # language=typescript
    assert (
        file2.content
        == """
export { bar } from 'file3'
import { externalDep } from "./file1";

function foo(): string {
    return fooDep() + 1 + "🐍";
}

function fooDep(): string {
    return 24 + "🐲";
}
"""
    )

    # language=typescript
    assert (
        file3.content
        == """
import { externalDep } from 'file1';
import { bar } from "./file2";

function baz(): string {
    return bar() + "🤯" + 1;
}

export function barDep(): string {
    return "😀";
}

export function bar(): string {
    return externalDep() + barDep() + "🔗";
}
"""
    )


def test_unicode_rename_local(tmpdir) -> None:
    # language=typescript
    content = """
function helperFuncA(paramA: string): string {
    return "✨" + paramA;
}

function helperFuncB(paramA: string): string {
    return "🎊" + paramA;
}

function mainFunc(inputId: string): string {
    const varA = inputId;
    const varB = "🍃";
    const idA = varA.attrA;
    const resultA = helperFuncA(varA);
    const varC = helperFuncB(varB + "😑");
    const config = {
        id: varB.attrA ? varB.attrA : null,
    };
    return varA;
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file.ts": content},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        for function in codebase.functions:
            local_vars = function.code_block.get_local_var_assignments("var", fuzzy_match=True)
            for local_var in local_vars:
                local_var.rename(local_var.name.replace("var", "renamedVar"))

    # language=typescript
    expected_content = """
function helperFuncA(paramA: string): string {
    return "✨" + paramA;
}

function helperFuncB(paramA: string): string {
    return "🎊" + paramA;
}

function mainFunc(inputId: string): string {
    const renamedVarA = inputId;
    const renamedVarB = "🍃";
    const idA = renamedVarA.attrA;
    const resultA = helperFuncA(renamedVarA);
    const renamedVarC = helperFuncB(renamedVarB + "😑");
    const config = {
        id: renamedVarB.attrA ? renamedVarB.attrA : null,
    };
    return renamedVarA;
}
"""
    assert codebase.get_file("file.ts").content == expected_content


def test_unicode_rename_function(tmpdir) -> None:
    # language=typescript
    content1 = """
import { foo } from "./file2";

function externalUsage(): string {
    return "🎇" + foo();
}
"""
    # language=typescript
    content2 = """
function baz(): string {
    return foo() + "🤯" + 1;
}

export function foo(): string {
    return fooDep() + 1 + "🐍";
}

function fooDep(): string {
    return 24 + "🐲";
}

function bar(): string {
    return "🦄" + foo() + "🔗";
}
"""
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"file1.ts": content1, "file2.ts": content2},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")

        foo = file2.get_function("foo")
        foo.rename("fooRenamed")

    # language=typescript
    assert (
        file1.content
        == """
import { fooRenamed } from "./file2";

function externalUsage(): string {
    return "🎇" + fooRenamed();
}
"""
    )
    # language=typescript
    assert (
        file2.content
        == """
function baz(): string {
    return fooRenamed() + "🤯" + 1;
}

export function fooRenamed(): string {
    return fooDep() + 1 + "🐍";
}

function fooDep(): string {
    return 24 + "🐲";
}

function bar(): string {
    return "🦄" + fooRenamed() + "🔗";
}
"""
    )
