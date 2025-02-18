from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_get_reexported_exports(tmpdir):
    # language=typescript
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "index.ts": """
                export {helper1, helper2} from "./importer";
                export { foo } from "foo"
                export * from "external-lib";
            """,
            "importer.ts": """
                import { helper1, helper2} from "./utils";
            """,
            "utils.ts": """
                export const helper1 = () => {};
                export const helper2 = () => {};
            """,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        assert len(file.export_statements) == 3
        exports_1 = file.export_statements[0]
        reexports = exports_1.reexports
        assert len(reexports) == 2
        assert reexports[0].name == "helper1"
        assert reexports[1].name == "helper2"
        exports_2 = file.export_statements[1]
        reexports = exports_2.reexports
        assert len(reexports) == 0
        exports_3 = file.export_statements[2]
        reexports = exports_3.reexports
        assert len(reexports) == 0


def test_get_reexported_export_with_external_module_on_export(tmpdir):
    # language=typescript
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "index.ts": """
                    export {helper1, helper2, foo} from "./importer";
                    export * from "external-lib";
                """,
            "importer.ts": """
                    import { helper1, helper2} from "./utils";
                    export { foo } from "./foo"
                """,
            "utils.ts": """
                    export const helper1 = () => {};
                    export const helper2 = () => {};
                """,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        assert len(file.export_statements) == 2
        exports = file.export_statements[0]
        reexports = exports.reexports
        # foo is a external module and should not be picked up
        assert len(reexports) == 2


def test_get_reexported_export_with_alias(tmpdir):
    # language=typescript
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "index.ts": """
                    export {helper1Alias, helper2Alias} from "./importer";
                """,
            "importer.ts": """
                    import { helper1 as helper1Alias, helper2 as helper2Alias} from "./utils";
                """,
            "utils.ts": """
                    export const helper1 = () => {};
                    export const helper2 = () => {};
                """,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        assert len(file.export_statements) == 1
        exports = file.export_statements[0]
        reexports = exports.reexports
        assert len(reexports) == 2
        assert reexports[0].name == "helper1Alias"
        assert reexports[1].name == "helper2Alias"
