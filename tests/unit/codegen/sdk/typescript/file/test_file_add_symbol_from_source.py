from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.assignment import Assignment
from codegen.sdk.typescript.function import TSFunction
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_add_symbol_from_source(tmpdir) -> None:
    # language=typescript
    file = """
function add_symbol_to_file() {
    let x = new Array([1,2,3,4,5,6,7,8,9,10]);
    return x
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": file}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        file.add_symbol_from_source(source="export const c = 1")

    symbol = file.get_symbol("c")
    codebase.ctx.commit_transactions()
    assert symbol.name == "c"
    assert isinstance(symbol, Assignment)
    assert "export const c = 1" in file.content
    assert symbol.is_exported

    file.add_symbol_from_source(source="const b = 1")
    codebase.ctx.commit_transactions()
    symbol = file.get_symbol("b")
    assert symbol.name == "b"
    assert isinstance(symbol, Assignment)
    assert "export const b = 1" not in file.content
    assert "const b = 1" in file.content
    assert not symbol.is_exported

    # language=typescript
    new_symbol_source = """function addSymbolToFile() {
        let x = new Array([1,2,3,4,5,6,7,8,9,10]);
        return x
    }
        """

    file.add_symbol_from_source(source=f"export {new_symbol_source}")
    codebase.ctx.commit_transactions()
    symbol = file.get_symbol("addSymbolToFile")
    assert symbol.name == "addSymbolToFile"
    assert symbol.is_exported
    assert isinstance(symbol, TSFunction)
    assert "export function addSymbolToFile" in file.content
    assert "const b = 1" in file.content


def test_add_symbol_from_source_global_var(tmpdir) -> None:
    FILENAME = "test_add_symbol_to_file.ts"
    # language=typescript
    FILE_CONTENT = """
    function foo(bar: number): number {
        return bar;
    }
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        file = codebase.get_file(FILENAME)
        file.add_symbol_from_source(source="export const c = 1;")

    symbol = file.get_symbol("c")

    assert symbol.name == "c"
    assert isinstance(symbol, Assignment)
    assert "const c = 1;" in file.content

    assert any([node.name == "c" for node in file.get_nodes()])
