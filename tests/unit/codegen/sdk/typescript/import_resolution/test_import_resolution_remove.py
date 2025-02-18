from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_remove_import_removes_from_file_imports(tmpdir) -> None:
    # language=typescript
    content = """
import a from 'b';  // test one
import { d } from 'b/c';  // test two
import { h as g, j as i } from 'd/f';  // test three
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")

        # =====[ Remove a ]=====
        imp = file.get_import("a")
        imp.remove()

    assert "import a from 'b';  // test one" not in imp.to_file.content
    assert imp not in imp.to_file.imports

    # =====[ Remove b/c ]=====
    imp = file.get_import("d")
    imp.remove()
    codebase.ctx.commit_transactions()
    assert "import { d } from 'b/c';  // test two" not in imp.to_file.content
    assert imp not in imp.to_file.imports

    # =====[ Remove d/f ]=====
    imp = file.get_import("g")
    imp.remove()
    codebase.ctx.commit_transactions()
    assert "import { j as i } from 'd/f';  // test three" in file.content
    assert imp not in file.imports


def test_remove_single_import_from_multiline(tmpdir) -> None:
    # language=typescript
    content = """
import {
    one,
    two,
    three as alias,
    four,
} from 'package';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imp = file.get_import("one")
        assert imp is not None
        imp.remove()
        two = file.get_import("two")
        assert two is not None
        two.remove()

    # language=typescript
    assert (
        file.content
        == """
import {
    three as alias,
    four,
} from 'package';
"""
    )


def test_remove_aliased_import_from_multiline(tmpdir) -> None:
    # language=typescript
    content = """
import {
    one,
    two,
    three as alias,
    four,
} from 'package';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imp = file.get_import("alias")
        assert imp is not None
        imp.remove()

    # language=typescript
    assert (
        file.content
        == """
import {
    one,
    two,
    four,
} from 'package';
"""
    )


def test_remove_all_imports_from_multiline(tmpdir) -> None:
    # language=typescript
    content = """
import {
    one,
    two,
    three,
    four,
} from 'package';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")

        for name in ["one", "two", "three", "four"]:
            imp = file.get_import(name)
            assert imp is not None
            imp.remove()

    # language=typescript
    assert (
        file.content.strip()
        == """
""".strip()
    )


def test_remove_single_import(tmpdir) -> None:
    # language=typescript
    content = """
import { one } from 'module1';
import { function1, function2 } from 'package1/module2';
import { Class1 } from 'package2/module3';
import { Class2 as Alias } from 'package3';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imp = file.get_import("function1")
        assert imp is not None
        imp.remove()

    assert (
        file.content.strip()
        == """
import { one } from 'module1';
import { function2 } from 'package1/module2';
import { Class1 } from 'package2/module3';
import { Class2 as Alias } from 'package3';
""".strip()
    )


def test_remove_multiline_imports(tmpdir) -> None:
    # language=typescript
    content = """
import {
    function1,
    function2,
    function3,
    function4
} from 'package1/module1';
import { module1 } from 'package2';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imp2 = file.get_import("function2")
        imp3 = file.get_import("function3")
        assert imp2 is not None and imp3 is not None
        imp2.remove()
        imp3.remove()

    assert (
        file.content.strip()
        == """
import {
    function1,
    function4
} from 'package1/module1';
import { module1 } from 'package2';
""".strip()
    )


def test_remove_entire_multiline_import(tmpdir) -> None:
    # language=typescript
    content = """
import {
    function1,
    function2,
    function3
} from 'package1/module1';
import { module1 } from 'package2';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imp1 = file.get_import("function1")
        imp2 = file.get_import("function2")
        imp3 = file.get_import("function3")
        assert imp1 is not None and imp2 is not None and imp3 is not None
        imp1.remove()
        imp2.remove()
        imp3.remove()

    assert (
        file.content.strip()
        == """
import { module1 } from 'package2';
""".strip()
    )


def test_remove_single_reexport(tmpdir) -> None:
    # language=typescript
    content = """
export { one, two, three } from 'module1';
export { four, five } from 'module2';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        exp = file.get_export("two")
        assert exp is not None
        exp.remove()

    assert (
        file.content.strip()
        == """
export { one, three } from 'module1';
export { four, five } from 'module2';
""".strip()
    )


def test_remove_multiline_reexports(tmpdir) -> None:
    # language=typescript
    content = """
export {
    one,
    two,
    three,
    four
} from 'module1';
export { five } from 'module2';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        exp2 = file.get_export("two")
        exp3 = file.get_export("three")
        assert exp2 is not None and exp3 is not None
        exp2.remove()
        exp3.remove()

    assert (
        file.content.strip()
        == """
export {
    one,
    four
} from 'module1';
export { five } from 'module2';
""".strip()
    )


def test_remove_entire_reexport_statement(tmpdir) -> None:
    # language=typescript
    content = """
export {
    one,
    two,
    three
} from 'module1';
export { four } from 'module2';
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        exp1 = file.get_export("one")
        exp2 = file.get_export("two")
        exp3 = file.get_export("three")
        assert exp1 is not None and exp2 is not None and exp3 is not None
        exp1.remove()
        exp2.remove()
        exp3.remove()

    assert (
        file.content.strip()
        == """
export { four } from 'module2';
""".strip()
    )
