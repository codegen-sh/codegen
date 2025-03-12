from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_get_symbol_in_tsx(tmpdir) -> None:
    # language=typescript jsx
    exporter_content = """
export function Component() {
    return <div>Hello World</div>
}
    """

    # language=typescript jsx
    importer_content = """
import { Component } from "./component"
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        programming_language=ProgrammingLanguage.TYPESCRIPT,
        files={"component.tsx": exporter_content, "importer.tsx": importer_content},
    ) as codebase:
        exporter_file = codebase.get_file("component.tsx")
        importer_file = codebase.get_file("importer.tsx")

        symbol = exporter_file.get_symbol("Component")
        assert len(symbol.symbol_usages) == 2
        assert symbol.symbol_usages == [exporter_file.get_export("Component"), importer_file.get_import("Component")]
