from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_global_var_single_var(tmpdir) -> None:
    # language=typescript
    content = """
let a: number = 1
var b = "string"
const c = {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT, verify_output=False) as codebase:
        file = codebase.get_file("file.ts")
        assert len(file.global_vars) == 3
        a = file.get_global_var("a")
        b = file.get_global_var("b")
        c = file.get_global_var("c")

        assert a.value == "1"
        assert b.value == '"string"'
        assert c.value == "{}"
        a.set_value("2")
        b.set_value('"new string"')
        c.set_value("{2.0}")

    assert file.get_global_var("a").value == "2"
    assert file.get_global_var("b").value == '"new string"'
    assert file.get_global_var("c").value == "{2.0}"
    # language=typescript
    assert (
        file.content
        == """
let a: number = 2
var b = "new string"
const c = {2.0}
    """
    )


def test_global_var_multiple_assignments(tmpdir) -> None:
    content = "let a = b = c = 0;"
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        assert len(file.global_vars) == 3
        a = file.get_global_var("a")
        b = file.get_global_var("b")
        c = file.get_global_var("c")

        assert a.value == "b = c = 0"
        assert b.value == "c = 0"
        assert c.value == "0"
        b.set_value("1")

    assert len(file.global_vars) == 2
    assert file.get_global_var("a").value == "b = 1"
    assert file.get_global_var("b").value == "1"
    assert file.content == "let a = b = 1;"


def test_global_var_multiple_in_line(tmpdir) -> None:
    content = "let x: number = 10, y: number = -1;"
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        assert len(file.global_vars) == 2
        x = file.get_global_var("x")
        y = file.get_global_var("y")

        assert x.value == "10"
        assert y.value == "-1"
        x.set_value("20")
        y.set_value("-2")

    assert file.get_global_var("x").value == "20"
    assert file.get_global_var("y").value == "-2"


def test_global_var_no_value(tmpdir) -> None:
    # language=typescript
    content = """
let x: number;
let a: number, b: string, c: boolean;
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        assert len(file.global_vars) == 4
        x = file.get_global_var("x")
        a = file.get_global_var("a")
        b = file.get_global_var("b")
        c = file.get_global_var("c")

        assert all(x.value is None for x in file.global_vars)

        x.set_value("10")
        a.set_value("20")
        b.set_value('"string"')
        c.set_value("true")

    assert file.get_global_var("x").value == "10"
    assert file.get_global_var("a").value == "20"
    assert file.get_global_var("b").value == '"string"'
    assert file.get_global_var("c").value == "true"
    # language=typescript
    assert (
        file.content
        == """
let x: number = 10;
let a: number = 20, b: string = "string", c: boolean = true;
"""
    )


def test_global_var_destructuring_assignment(tmpdir) -> None:
    # language=typescript
    content = """let [a, b, c] = [1, "two", true];"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        assert len(file.global_vars) == 3
        a = file.get_global_var("a")
        b = file.get_global_var("b")
        c = file.get_global_var("c")

        assert a.value == '[1, "two", true]'
        assert b.value == '[1, "two", true]'
        assert c.value == '[1, "two", true]'
        a.set_value('[2, "three", false]')

    assert len(file.global_vars) == 3
    # language=typescript
    assert file.content == """let [a, b, c] = [2, "three", false];"""
