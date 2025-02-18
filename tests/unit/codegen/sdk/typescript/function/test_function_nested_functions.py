from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_nested_base(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
function parent() {
    function a() {
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        parent = codebase.get_symbol("parent")
        assert len(parent.nested_functions) == 1
        assert parent.nested_functions[0].name == "a"


def test_nested_parsing(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
function a() {
}

function parent() {
    function b() {
    }

    let c_1 = function() {}
    let c_2 = () => {}
    const c_3 = function() {}
    const c_4 = () => {}

    function d() {
        function e() {
        }
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        parent = codebase.get_symbol("parent")
        assert len(parent.nested_functions) == 6
        assert {f.name for f in parent.nested_functions} == {"b", "c_1", "c_2", "c_3", "c_4", "d"}


def test_usages(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
function a() {
}

function parent() {
    function b() {
    }

    a();
    b();
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        parent = codebase.get_symbol("parent")
        a = codebase.get_symbol("a")
        assert len(a.symbol_usages) == 1
        assert a.symbol_usages[0] == parent

        b = parent.nested_functions[0]
        assert len(b.symbol_usages) == 1
        assert b.symbol_usages[0] == parent


def test_dependencies(tmpdir) -> None:
    FILENAME = "function_test.ts"
    # language=typescript
    FILE_CONTENT = """
function a() {
}

function parent() {
    function b() {
        a()
    }

    b();
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        parent = codebase.get_symbol("parent")
        a = codebase.get_symbol("a")
        assert len(a.dependencies) == 0

        b = parent.nested_functions[0]
        assert len(b.dependencies) == 1
        assert b.dependencies[0] == a

        assert len(parent.dependencies) == 1
        assert {d.name for d in parent.dependencies} == {"a"}
