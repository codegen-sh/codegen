from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.dataclasses.usage import UsageType
from codegen.sdk.enums import ImportType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_exportable_usage_symbol_export(tmpdir) -> None:
    # language=typescript
    content1 = """
function foo() {}
function fuzz() {}

export { foo as foop, fuzz };
    """
    # language=typescript
    content2 = """
import * as file1 from './file1';

function bar() {
    return file1.foop();
}

function zoo() {
    return file1.fuzz();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        foo = file1.get_symbol("foo")
        fuzz = file1.get_symbol("fuzz")

        bar = file2.get_symbol("bar")
        imp = file2.get_import("file1")
        zoo = file2.get_symbol("zoo")
        assert imp.namespace == "file1"
        assert foo.exported_name == "foop"
        assert fuzz.exported_name == "fuzz"
        assert set(foo.symbol_usages(UsageType.DIRECT)) == {foo.export}
        assert set(foo.symbol_usages) == {foo.export, bar}
        assert set(fuzz.symbol_usages(UsageType.DIRECT)) == {fuzz.export}
        assert set(fuzz.symbol_usages(usage_types=UsageType.CHAINED | UsageType.DIRECT)) == {fuzz.export, zoo}
        assert set(fuzz.symbol_usages) == {fuzz.export, zoo}
        assert len(foo.symbol_usages) == 2
        assert len(fuzz.symbol_usages) == 2
        assert len(foo.symbol_usages) == len(fuzz.symbol_usages) == 2


def test_exportable_usage_via_symbol_default_export(tmpdir) -> None:
    # language=typescript
    content1 = """
function foo() {}

export default foo;
    """
    # language=typescript
    content2 = """
import foo from './export1';

function bar() {
    return foo();
}
function zoo() {
    return 12;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"export1.ts": content1, "export2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("export1.ts")
        file2 = codebase.get_file("export2.ts")
        foo = file1.get_symbol("foo")
        bar = file2.get_symbol("bar")
        imp = file2.get_import("foo")
        assert imp.namespace is None
        assert foo.exported_name == "foo"
        assert len(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert len(foo.symbol_usages) == 3
        assert set(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo.export, imp}
        assert set(foo.symbol_usages(usage_types=UsageType.DIRECT | UsageType.INDIRECT)) == {foo.export, imp, bar}
        assert set(foo.symbol_usages) == {foo.export, imp, bar}


def test_exportable_usage_via_object_default_export(tmpdir) -> None:
    # language=typescript
    content1 = """
function foo() {}
function fuzz() {}

export default { foo, fizz: fuzz };
    """
    # language=typescript
    content2 = """
import file1 from './file1';

function bar() {
    return file1.foo();
}

function zoo() {
    return file1.fizz();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        foo = file1.get_symbol("foo")
        fuzz = file1.get_symbol("fuzz")

        bar = file2.get_symbol("bar")
        zoo = file2.get_symbol("zoo")
        imp = file2.get_import("file1")
        assert imp.namespace == "file1"
        assert foo.exported_name == "foo"
        assert fuzz.exported_name == "fizz"
        assert set(foo.symbol_usages(UsageType.DIRECT)) == {foo.export}
        assert set(foo.symbol_usages(usage_types=UsageType.DIRECT | UsageType.INDIRECT | UsageType.CHAINED)) == {foo.export, bar}
        assert set(foo.symbol_usages) == {foo.export, bar}
        assert set(fuzz.symbol_usages) == {fuzz.export, zoo}
        assert set(fuzz.symbol_usages(usage_types=UsageType.DIRECT | UsageType.INDIRECT)) == {fuzz.export}
        assert set(fuzz.symbol_usages) == {fuzz.export, zoo}
        assert len(foo.symbol_usages(UsageType.DIRECT)) == len(fuzz.symbol_usages(UsageType.DIRECT)) == 1
        assert len(foo.symbol_usages) == len(fuzz.symbol_usages) == 2


def test_exportable_usage_via_named_and_default_exports(tmpdir) -> None:
    # language=typescript
    content1 = """
function foo() {}
function fuzz() {}

export { foo as floop };
export default { buzz: fuzz };
    """
    # language=typescript
    content2 = """
import file1, { floop } from './file1';

function bar() {
    return floop() + file1.buzz();
}
function zoo() {
    return 12;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        foo = file1.get_symbol("foo")
        fuzz = file1.get_symbol("fuzz")
        bar = file2.get_symbol("bar")
        file1_imp = file2.get_import("file1")
        floop_imp = file2.get_import("floop")

        assert file1_imp.namespace == "file1"
        assert floop_imp.namespace is None
        assert foo.exported_name == "floop"
        assert fuzz.exported_name == "buzz"

        assert set(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo.export, floop_imp}
        assert set(foo.symbol_usages) == {foo.export, floop_imp, bar}
        assert set(fuzz.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {fuzz.export, bar}
        assert set(fuzz.symbol_usages) == {fuzz.export, bar}
        assert len(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == len(fuzz.symbol_usages) == 2
        assert len(foo.symbol_usages) == 3
        assert len(fuzz.symbol_usages) == 2

        assert set(foo.export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {floop_imp}
        assert set(foo.export.symbol_usages) == {floop_imp, bar}
        assert set(fuzz.export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {bar}
        assert set(fuzz.export.symbol_usages) == {bar}
        assert set(floop_imp.symbol_usages) == {bar}
        assert set(floop_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {bar}
        assert set(file1_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {bar}
        assert set(file1_imp.symbol_usages) == {bar}


def test_exportable_usages_via_wildcard_export(tmpdir) -> None:
    # language=typescript
    content1 = """
function foo() {}
function fuzz() {}
export { foo as floop, fuzz as fizz };
    """
    # language=typescript
    content2 = """
export * from './file1';
    """
    # language=typescript
    content3 = """
import { floop, fizz } from './file2';

function bar() {
    return floop() + fizz();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content1, "file2.ts": content2, "file3.ts": content3}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")
        foo = file1.get_symbol("foo")
        fuzz = file1.get_symbol("fuzz")
        bar = file3.get_symbol("bar")

        wildcard_imp = file2.imports[0]
        wildcard_export = file2.exports[0]
        floop_imp = file3.get_import("floop")
        fuzz_imp = file3.get_import("fizz")

        assert floop_imp.namespace is None
        assert foo.exported_name == "floop"
        assert fuzz.exported_name == "fizz"
        assert set(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo.export}
        assert set(foo.symbol_usages) == {foo.export, floop_imp, bar}
        assert set(fuzz.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {fuzz.export}
        assert set(fuzz.symbol_usages) == {fuzz.export, fuzz_imp, bar}
        assert len(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == len(fuzz.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 1
        assert len(foo.symbol_usages) == len(fuzz.symbol_usages) == 3

        assert set(foo.export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == set()
        assert set(foo.export.symbol_usages) == {floop_imp, bar}
        assert set(fuzz.export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == set()
        assert set(fuzz.export.symbol_usages) == {fuzz_imp, bar}
        assert len(foo.export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == len(fuzz.export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 0
        assert len(foo.export.symbol_usages) == len(fuzz.export.symbol_usages) == 2

        assert set(wildcard_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {wildcard_export}
        assert set(wildcard_imp.symbol_usages) == {wildcard_export, floop_imp, fuzz_imp, bar}
        assert set(wildcard_export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {floop_imp, fuzz_imp}
        assert set(wildcard_export.symbol_usages) == {floop_imp, fuzz_imp, bar}
        assert len(wildcard_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 1
        assert len(wildcard_imp.symbol_usages) == 4
        assert len(wildcard_export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert len(wildcard_export.symbol_usages) == 3


def test_usages_named_export_aliased_twice(tmpdir) -> None:
    # language=typescript
    content = """
function foo() {}
export { foo as foo_rename1 };
    """
    # language=typescript
    content2 = """
import { foo_rename1 as foo_rename2 } from './file1';
export { foo_rename2 as foo_rename3 };
    """
    # language=typescript
    content3 = """
import { foo_rename3 as foo_rename4 } from './file2';

function bar() {
    return foo_rename4();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content, "file2.ts": content2, "file3.ts": content3}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")
        foo = file1.get_symbol("foo")
        foo_rename1_export = file1.get_export("foo_rename1")
        foo_rename2_imp = file2.get_import("foo_rename2")
        foo_rename3_export = file2.get_export("foo_rename3")
        foo_rename4_imp = file3.get_import("foo_rename4")
        bar = file3.get_function("bar")

        assert foo.exported_name == "foo_rename1"
        assert foo_rename1_export.exported_name == "foo_rename1"
        assert foo_rename2_imp.exported_name == "foo_rename3"
        assert foo_rename3_export.exported_name == "foo_rename3"
        assert foo_rename4_imp.exported_name is None

        assert set(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo.export, foo_rename2_imp}
        assert set(foo.symbol_usages) == {foo.export, foo_rename2_imp, foo_rename3_export, foo_rename4_imp, bar}
        assert set(foo_rename2_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo_rename2_imp.export, foo_rename4_imp}
        assert set(foo_rename2_imp.symbol_usages) == {foo_rename2_imp.export, foo_rename4_imp, bar}
        assert set(foo_rename3_export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo_rename4_imp}
        assert set(foo_rename3_export.symbol_usages) == {foo_rename4_imp, bar}
        assert set(foo_rename4_imp.symbol_usages) == {bar}
        assert set(foo_rename4_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {bar}

        assert len(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert len(foo.symbol_usages) == 5
        assert len(foo_rename2_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert len(foo_rename2_imp.symbol_usages) == 3
        assert len(foo_rename3_export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 1
        assert len(foo_rename3_export.symbol_usages) == 2
        assert len(foo_rename4_imp.symbol_usages) == 1
        assert len(foo_rename4_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 1


def test_usages_module_export_aliased_twice(tmpdir) -> None:
    # language=typescript
    content = """
function foo() {}
export { foo as foo_rename1 };
    """
    # language=typescript
    content2 = """
import * as file1_rename1 from './file1';
export { file1_rename1 as file1_rename2 };
    """
    # language=typescript
    content3 = """
import { file1_rename2 as file1_rename3 } from './file2';

function bar() {
    return file1_rename3.foo_rename1();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.ts": content, "file2.ts": content2, "file3.ts": content3}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        file3 = codebase.get_file("file3.ts")
        foo = file1.get_symbol("foo")
        foo_rename1_export = file1.get_export("foo_rename1")
        file1_rename1_imp = file2.get_import("file1_rename1")
        file1_rename2_export = file2.get_export("file1_rename2")
        file1_rename3_imp = file3.get_import("file1_rename3")
        bar = file3.get_function("bar")

        assert foo.exported_name == "foo_rename1"
        assert foo_rename1_export.exported_name == "foo_rename1"
        assert file1_rename1_imp.namespace == "file1_rename1"
        assert file1_rename1_imp.exported_name == "file1_rename2"
        assert file1_rename2_export.exported_name == "file1_rename2"
        assert file1_rename3_imp.namespace == "file1_rename3"
        assert file1_rename3_imp.exported_name is None

        assert set(foo.symbol_usages(UsageType.DIRECT)) == {foo.export}
        assert set(foo.symbol_usages) == {foo.export, bar}
        assert set(foo_rename1_export.symbol_usages) == {bar}
        assert set(foo_rename1_export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {bar}
        assert set(file1_rename1_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {file1_rename1_imp.export, file1_rename3_imp}
        assert set(file1_rename1_imp.symbol_usages) == {file1_rename1_imp.export, file1_rename3_imp, bar}
        assert set(file1_rename2_export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {file1_rename3_imp}
        assert set(file1_rename2_export.symbol_usages) == {file1_rename3_imp, bar}
        assert set(file1_rename3_imp.symbol_usages) == {bar}
        assert set(file1_rename3_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {bar}
        assert len(foo.symbol_usages(UsageType.DIRECT)) == 1
        assert len(foo.symbol_usages) == 2
        assert len(foo_rename1_export.symbol_usages) == 1
        assert len(foo_rename1_export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 1
        assert len(file1_rename1_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert len(file1_rename1_imp.symbol_usages) == 3
        assert len(file1_rename2_export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 1
        assert len(file1_rename2_export.symbol_usages) == 2
        assert len(file1_rename3_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 1
        assert len(file1_rename3_imp.symbol_usages) == 1


def test_exportable_usages_default_symbol(tmpdir) -> None:
    # language=typescript
    content1 = """
export default function foo() {}
    """
    # language=typescript
    content2 = """
import randomName from './file1.js'

function someFunction() {
    return randomName();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.js": content1, "file2.js": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.js")
        file2 = codebase.get_file("file2.js")
        foo = file1.get_function("foo")
        imp = file2.get_import("randomName")
        assert imp.import_type == ImportType.DEFAULT_EXPORT
        assert set(foo.symbol_usages) == {foo.export, imp, file2.get_function("someFunction")}


def test_exportable_usage_via_wildcard_import_default_export(tmpdir) -> None:
    # language=typescript
    content1 = """
export default function foo() {}
    """
    # language=typescript
    content2 = """
import * as file1Alias from './file1.js'

function someFunction() {
    return file1Alias.default();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.js": content1, "file2.js": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.js")
        file2 = codebase.get_file("file2.js")
        foo = file1.get_symbol("foo")
        some_function = file2.get_symbol("someFunction")
        wildcard_imp = file2.get_import("file1Alias")

        assert wildcard_imp.namespace == "file1Alias"
        assert foo.exported_name == "foo"
        assert set(foo.symbol_usages(UsageType.DIRECT)) == {foo.export}
        assert set(foo.symbol_usages) == {foo.export, some_function}
        assert set(wildcard_imp.symbol_usages) == {some_function}
        assert set(wildcard_imp.symbol_usages) == {some_function}
        assert len(foo.symbol_usages(UsageType.DIRECT)) == 1
        assert len(foo.symbol_usages) == 2


def test_exportable_usage_via_reexport(tmpdir) -> None:
    # language=typescript
    content1 = """
export function foo() {}
    """
    # language=typescript
    content2 = """
export { foo as default } from './file1.js'
    """
    # language=typescript
    content3 = """
import someRandomFooName from './file2.js'

function someFunction() {
    return someRandomFooName();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.js": content1, "file2.js": content2, "file3.js": content3}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.js")
        file2 = codebase.get_file("file2.js")
        file3 = codebase.get_file("file3.js")
        foo = file1.get_symbol("foo")
        foo_reexport = file2.get_export("default")
        foo_imp = file2.get_import("default")
        file1_imp = file3.get_import("someRandomFooName")

        assert foo_imp.import_type == ImportType.NAMED_EXPORT
        assert foo.exported_name == "foo"
        assert foo_imp.namespace is None
        assert file1_imp.namespace is None
        assert set(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo.export, foo_imp}
        assert set(foo.symbol_usages) == {foo.export, foo_imp, foo_reexport, file1_imp, file3.get_function("someFunction")}
        assert len(foo.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert len(foo.symbol_usages) == 5
        assert set(foo.export.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo_imp}
        assert set(foo.export.symbol_usages) == {foo_imp, foo_reexport, file1_imp, file3.get_function("someFunction")}
        assert set(foo_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {foo_reexport, file1_imp}
        assert set(foo_imp.symbol_usages) == {foo_reexport, file1_imp, file3.get_function("someFunction")}
        assert set(foo_reexport.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {file1_imp}
        assert set(foo_reexport.symbol_usages) == {file1_imp, file3.get_function("someFunction")}
        assert set(file1_imp.symbol_usages) == {file3.get_function("someFunction")}
        assert set(file1_imp.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {file3.get_function("someFunction")}


def test_exportable_usage_namespace_import(tmpdir) -> None:
    # language=typescript
    content1 = """
export function foo() {}
export function bar() {}
    """
    # language=typescript
    content2 = """
import * as myAlias from './file1'

function zoo() {
    myAlias.foo();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.js": content1, "file2.js": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.js")
        file2 = codebase.get_file("file2.js")
        foo = file1.get_function("foo")
        bar = file1.get_function("bar")
        zoo = file2.get_function("zoo")
        imp = file2.get_import("myAlias")

        assert set(imp.symbol_usages) == {zoo}
        assert set(imp.symbol_usages) == {zoo}
        assert set(foo.symbol_usages(UsageType.DIRECT)) == {foo.export}
        assert set(foo.symbol_usages) == {foo.export, zoo}
        assert set(bar.symbol_usages) == {bar.export}
        assert set(bar.symbol_usages) == {bar.export}
        assert set(foo.export.symbol_usages(UsageType.DIRECT)) == set()
        assert set(foo.export.symbol_usages) == {zoo}
        assert set(bar.export.symbol_usages) == set()
        assert set(bar.export.symbol_usages) == set()


def test_exportable_usage_default_module_import(tmpdir) -> None:
    # language=typescript
    content1 = """
export default function myDefaultFunction() {}
export function myFunction() {}
    """
    # language=typescript
    content2 = """
import myDefaultFunction from './file1'
import * as file1Alias from './file1.js'

function zoo() {
    file1Alias.default();
}

function bar() {
    return file1Alias.myFunction();
}

function someOtherFunction() {
    return myDefaultFunction();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.js": content1, "file2.js": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.js")
        file2 = codebase.get_file("file2.js")
        default_function = file1.get_function("myDefaultFunction")
        function = file1.get_function("myFunction")
        imp = file2.get_import("myDefaultFunction")
        wildcard_imp = file2.get_import("file1Alias")
        zoo = file2.get_function("zoo")
        bar = file2.get_function("bar")
        some_other_function = file2.get_function("someOtherFunction")

        assert imp.namespace is None
        assert imp not in set(function.symbol_usages)
        assert wildcard_imp not in set(function.symbol_usages)
        assert imp in set(default_function.symbol_usages)
        assert wildcard_imp not in set(default_function.symbol_usages)
        assert zoo in set(default_function.symbol_usages)
        assert zoo not in set(function.symbol_usages)
        assert some_other_function in set(default_function.symbol_usages)
        assert some_other_function not in set(function.symbol_usages)
        assert bar not in set(default_function.symbol_usages)
        assert bar in set(function.symbol_usages)


def test_exportable_usage_default_export_declared_symbol(tmpdir) -> None:
    # language=typescript
    content1 = """
import { bar } from './file2.js'

export default foo(() => {bar()});
"""
    # language=typescript
    content2 = """
export function bar() {}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"file1.js": content1, "file2.js": content2}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file1 = codebase.get_file("file1.js")
        file2 = codebase.get_file("file2.js")
        bar = file2.get_function("bar")
        foo_exp = file1.exports[0]
        foo = foo_exp.value.args[0].value
        imp = file1.get_import("bar")

        assert set(bar.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == {bar.export, imp}
        assert set(bar.symbol_usages) == {bar.export, imp, foo, foo_exp}
        assert len(bar.call_sites) == 1
        assert len(bar.symbol_usages(UsageType.DIRECT | UsageType.CHAINED)) == 2
        assert len(bar.symbol_usages) == 4


def test_exportable_usage_in_export_declared_value(tmpdir) -> None:
    # language=typescript
    content1 = """
export function foo(): void {}
"""
    # language=typescript
    content2 = """
export default test({
    run() {
        const somethingElse = import("somewhereElse");
        const myFile = import("file1");
        myFile.foo();
    }
})
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"file1.ts": content1, "file2.ts": content2}) as codebase:
        file1 = codebase.get_file("file1.ts")
        file2 = codebase.get_file("file2.ts")
        foo = file1.get_function("foo")
        assert len(foo.call_sites) == 1
        assert foo.call_sites[0].source == "myFile.foo()"


def test_exportable_usage_through_reexport_chain(tmpdir) -> None:
    # language=typescript
    content1 = """
export function foo() {}
"""
    # language=typescript
    content2 = """
export * from "./thing2";
export * from "./thing";
"""
    # language=typescript
    content3 = """
import {foo} from "libs"

foo()
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"libs/thing.ts": content1, "libs/index.ts": content2, "main.ts": content3}) as codebase:
        foo = codebase.get_function("foo")
        main = codebase.get_file("main.ts")
        imp = main.imports[0]
        assert set(foo.symbol_usages) == {main, imp, foo.export}
