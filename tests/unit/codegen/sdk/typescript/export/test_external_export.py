from typing import TYPE_CHECKING

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage

if TYPE_CHECKING:
    from codegen.sdk.typescript.file import TSFile


def test_is_external_export_true(tmpdir):
    # language=typescript
    content = """
    export { default as React } from "react";
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"index.ts": content},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        assert len(file.exports) == 1
        assert file.exports[0].is_external_export is True


def test_is_external_export_false(tmpdir):
    # language=typescript
    content = """
    export { foo } from "./foo";
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "index.ts": content,
            "foo.ts": "export const foo = 42;",
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        assert len(file.exports) == 1
        assert file.exports[0].is_external_export is False


def test_multiple_external_exports(tmpdir):
    # language=typescript
    content = """
    export { default as React } from "react";
    export { useState, useEffect } from "react";
    export type { ReactNode } from "react";
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={"index.ts": content},
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        assert len(file.exports) == 4  # One export for each symbol: React, useState, useEffect, ReactNode
        assert all(export.is_external_export for export in file.exports)


def test_mixed_internal_external_exports(tmpdir):
    # language=typescript
    content = """
    export { default as lodash } from "lodash";
    export { helper } from "./utils";
    export { type User } from "./types";
    """
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "index.ts": content,
            "utils.ts": "export const helper = () => {};",
            "types.ts": "export type User = { id: string; name: string; };",
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        assert len(file.exports) == 3
        assert file.exports[0].is_external_export is True
        assert file.exports[1].is_external_export is False
        assert file.exports[2].is_external_export is False


def test_nested_reexports(tmpdir):
    # language=typescript
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "index.ts": 'export { UserService } from "./services";',
            "services/index.ts": 'export { UserService } from "./user.service";',
            "services/user.service.ts": """
                import { User } from "../types";
                export class UserService {
                    getUser(): User { return { id: "1", name: "Test" }; }
                }
            """,
            "types.ts": "export type User = { id: string; name: string; };",
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        services_file: TSFile = codebase.get_file("services/index.ts")

        assert len(file.exports) == 1
        assert file.exports[0].is_external_export is False
        assert len(services_file.exports) == 1
        assert services_file.exports[0].is_external_export is False


def test_wildcard_exports(tmpdir):
    # language=typescript
    with get_codebase_session(
        tmpdir=tmpdir,
        files={
            "index.ts": """
                export * from "./utils";
                export * from "external-lib";
            """,
            "utils.ts": """
                export const helper1 = () => {};
                export const helper2 = () => {};
            """,
        },
        programming_language=ProgrammingLanguage.TYPESCRIPT,
    ) as codebase:
        file: TSFile = codebase.get_file("index.ts")
        assert len(file.exports) == 2
        assert file.exports[0].is_external_export is False
        assert file.exports[1].is_external_export is True
