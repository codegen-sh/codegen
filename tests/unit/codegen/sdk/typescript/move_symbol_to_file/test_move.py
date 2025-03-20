import platform

import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


class TestBasicMoveToFile:
    """Test basic function move functionality without imports, using multiple strategies."""

    def test_basic_move(self, tmpdir) -> None:
        """Test basic function move without imports."""
        # language=typescript
        source_content = """
        export function targetFunction() {
            return "Hello World";
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)
            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=False)

        assert "targetFunction" not in source_file.content
        assert "export function targetFunction" in dest_file.content

    def test_update_all_imports_basic(self, tmpdir) -> None:
        """Test update_all_imports strategy updates imports in all dependent files."""
        # language=typescript
        source_content = """
        export function targetFunction() {
            return "Hello World";
        }
        """

        usage_content = """
        import { targetFunction } from './source';
        const value = targetFunction();
        """

        files = {
            "source.ts": source_content,
            "destination.ts": "",
            "usage.ts": usage_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file("destination.ts")
            usage_file = codebase.get_file("usage.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=False, strategy="update_all_imports")

        assert "targetFunction" not in source_file.content
        assert "export function targetFunction" in dest_file.content
        assert "import { targetFunction } from 'destination'" in usage_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_add_back_edge_basic(self, tmpdir) -> None:
        """Test add_back_edge strategy - adds import in source file and re-exports the moved symbol."""
        # language=typescript
        source_content = """
        export function targetFunction() {
            return "Hello World";
        }
        """

        files = {
            "source.ts": source_content,
            "destination.ts": "",
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file("destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=False, strategy="add_back_edge")

        assert "import { targetFunction } from 'destination'" in source_file.content
        assert "export { targetFunction }" in source_file.content
        assert "export function targetFunction" in dest_file.content

    def test_update_all_imports_with_dependencies(self, tmpdir) -> None:
        """Test update_all_imports strategy with dependencies."""
        # language=typescript
        source_content = """
        import { helperUtil } from './utils';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        files = {
            "source.ts": source_content,
            "destination.ts": "",
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file("destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "import { helperUtil } from './utils'" not in source_file.content
        assert "import { helperUtil } from './utils'" in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_add_back_edge_with_dependencies(self, tmpdir) -> None:
        """Test add_back_edge strategy with dependencies."""
        # language=typescript
        source_content = """
        import { helperUtil } from './utils';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        files = {
            "source.ts": source_content,
            "destination.ts": "",
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file("destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="add_back_edge")

        assert "import { targetFunction } from 'destination'" in source_file.content
        assert "import { helperUtil } from './utils'" not in source_file.content
        assert "import { helperUtil } from './utils'" in dest_file.content


class TestMoveToFileImports:
    """Test moving functions with various import scenarios."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_remove_unused_imports(self, tmpdir) -> None:
        """Test that unused imports are removed when cleanup_unused_imports=True."""
        # language=typescript
        source_content = """
        import { helperUtil } from './utils';
        import { otherUtil } from './other';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        files = {
            "source.ts": source_content,
            "destination.ts": "",
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file("destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports", cleanup_unused_imports=True)

        # Unused import should be removed
        assert "import { otherUtil } from './other'" not in source_file.content
        # Used import should move to destination
        assert "import { helperUtil } from './utils'" in dest_file.content

    def test_keep_unused_imports(self, tmpdir) -> None:
        """Test that unused imports are kept when cleanup_unused_imports=False."""
        # language=typescript
        source_content = """
        import { helperUtil } from './utils';
        import { otherUtil } from './other';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        files = {
            "source.ts": source_content,
            "destination.ts": "",
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file("destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports", cleanup_unused_imports=False)

        # All imports should be kept in source
        assert "import { helperUtil } from './utils'" in source_file.content
        assert "import { otherUtil } from './other'" in source_file.content
        # Used import should also be in destination
        assert "import { helperUtil } from './utils'" in dest_file.content

    def test_used_imports_always_move(self, tmpdir) -> None:
        """Test that used imports always move to destination regardless of remove_unused_imports flag."""
        # language=typescript
        source_content = """
        import { helperUtil } from './utils';
        import { otherUtil } from './other';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        files = {
            "source.ts": source_content,
            "destination.ts": "",
        }

        for remove_unused in [True, False]:
            with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
                source_file = codebase.get_file("source.ts")
                dest_file = codebase.get_file("destination.ts")

                target_function = source_file.get_function("targetFunction")
                target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports", cleanup_unused_imports=remove_unused)

        # Used import should always move to destination
        assert "import { helperUtil } from './utils'" in dest_file.content


class TestMoveToFileImportVariations:
    """Test moving functions with various import scenarios."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_module_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses module imports (import * as)"""
        # language=typescript
        source_content = """
        import * as utils from './utils';
        import * as unused from './unused';

        export function targetFunction() {
            return utils.helperUtil("test");
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "import * as utils from './utils'" not in source_file.content
        assert "import * as unused from './unused'" not in source_file.content
        assert "import * as utils from './utils'" in dest_file.content

    def test_move_with_side_effect_imports(self, tmpdir) -> None:
        """Test moving a symbol that has side effect imports"""
        # language=typescript
        source_content = """
        import './styles.css';
        import './polyfills';
        import { helperUtil } from './utils';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Side effect imports should remain in source
        assert "import './styles.css';" in source_file.content
        assert "import './polyfills';" in source_file.content
        # Used import should move
        assert "import { helperUtil } from './utils'" not in source_file.content
        assert "import { helperUtil } from './utils'" in dest_file.content

    def test_move_with_circular_dependencies(self, tmpdir) -> None:
        """Test moving a symbol that has circular dependencies"""
        # language=typescript
        source_content = """
        import { helperB } from './helper-b';

        export function targetFunction() {
            return helperB(innerHelper());
        }

        function innerHelper() {
            return "inner";
        }
        """

        # language=typescript
        helper_b_content = """
        import { targetFunction } from './source';

        export function helperB(value: string) {
            return targetFunction();
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
            "helper-b.ts": helper_b_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)
            helper_b_file = codebase.get_file("helper-b.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check circular dependency handling
        assert "import { helperB } from './helper-b'" not in source_file.content
        assert "import { helperB } from 'helper-b'" in dest_file.content
        assert "import { targetFunction } from 'destination'" in helper_b_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_reexports(self, tmpdir) -> None:
        """Test moving a symbol that is re-exported from multiple files"""
        # language=typescript
        source_content = """
        export function targetFunction() {
            return "test";
        }
        """

        # language=typescript
        reexport_a_content = """
        export { targetFunction } from './source';
        """

        # language=typescript
        reexport_b_content = """
        export { targetFunction as renamedFunction } from './source';
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
            "reexport-a.ts": reexport_a_content,
            "reexport-b.ts": reexport_b_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)
            reexport_a_file = codebase.get_file("reexport-a.ts")
            reexport_b_file = codebase.get_file("reexport-b.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check re-export updates
        assert "export { targetFunction } from './destination'" in reexport_a_file.content
        assert "export { targetFunction as renamedFunction } from './destination'" in reexport_b_file.content


class TestMoveToFileDecoratorsAndComments:
    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_decorators(self, tmpdir) -> None:
        """Test moving a symbol that has decorators"""
        # language=typescript
        source_content = """
        import { injectable } from 'inversify';
        import { validate } from './validators';

        @injectable()
        @validate()
        export function targetFunction() {
            return "test";
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "@injectable()" not in source_file.content
        assert "@validate()" not in source_file.content
        assert "@injectable()" in dest_file.content
        assert "@validate()" in dest_file.content
        assert "import { injectable } from 'inversify'" in dest_file.content
        assert "import { validate } from './validators'" in dest_file.content

    def test_move_with_jsdoc(self, tmpdir) -> None:
        """Test moving a symbol with JSDoc comments"""
        # language=typescript
        source_content = """
        import { SomeType } from './types';

        /**
         * @param {string} value - Input value
         * @returns {SomeType} Processed result
         */
        export function targetFunction(value: string): SomeType {
            return { value };
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "@param {string}" not in source_file.content
        assert "@returns {SomeType}" not in source_file.content
        assert "@param {string}" in dest_file.content
        assert "@returns {SomeType}" in dest_file.content
        assert "import { SomeType } from './types'" in dest_file.content


class TestMoveToFileDynamicImports:
    def test_move_with_dynamic_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses dynamic imports"""
        # language=typescript
        source_content = """
        export async function targetFunction() {
            const { helper } = await import('./helper');
            const utils = await import('./utils');
            return helper(utils.format("test"));
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "import('./helper')" not in source_file.content
        assert "import('./utils')" not in source_file.content
        assert "import('./helper')" in dest_file.content
        assert "import('./utils')" in dest_file.content

    def test_move_with_mixed_dynamic_static_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses both dynamic and static imports"""
        # language=typescript
        source_content = """
        import { baseHelper } from './base';

        export async function targetFunction() {
            const { dynamicHelper } = await import('./dynamic');
            return baseHelper(await dynamicHelper());
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "import { baseHelper }" not in source_file.content
        assert "import('./dynamic')" not in source_file.content
        assert "import { baseHelper }" in dest_file.content
        assert "import('./dynamic')" in dest_file.content


class TestMoveToFileNamedImports:
    """Test moving functions with named imports."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_named_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses named imports."""
        # language=typescript
        source_content = """
        import { foo, bar as alias, unused } from './module';

        export function targetFunction() {
            return foo(alias("test"));
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "import { foo, bar as alias" in dest_file.content
        assert "unused" not in dest_file.content
        assert "import { foo" not in source_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_default_and_named_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses both default and named imports."""
        # language=typescript
        source_content = """
        import defaultHelper, { namedHelper, unusedHelper } from './helper';

        export function targetFunction() {
            return defaultHelper(namedHelper("test"));
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "import defaultHelper, { namedHelper }" in dest_file.content
        assert "unusedHelper" not in dest_file.content
        assert "defaultHelper" not in source_file.content


class TestMoveToFileTypeImports:
    """Test moving functions with type imports."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_type_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses type imports."""
        # language=typescript
        source_content = """
        import type { Config } from './config';
        import type DefaultType from './types';
        import type { Used as Alias, Unused } from './utils';

        export function targetFunction(config: Config, type: DefaultType): Alias {
            return { value: config.value };
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check type imports are moved correctly
        assert "import type { Config }" in dest_file.content
        assert "import type DefaultType" in dest_file.content
        assert "import type { Used as Alias }" in dest_file.content
        assert "Unused" not in dest_file.content
        # Check original file cleanup
        assert "import type" not in source_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_mixed_type_value_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses both type and value imports."""
        # language=typescript
        source_content = """
        import type { Type1, Type2 } from './types';
        import { value1, value2 } from './values';

        export function targetFunction(t1: Type1): value1 {
            return value1(t1);
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check both type and value imports are handled
        assert "import type { Type1 }" in dest_file.content
        assert "Type2" not in dest_file.content
        assert "import { value1 }" in dest_file.content
        assert "value2" not in dest_file.content


class TestMoveToFileUsageUpdates:
    """Test updating import statements in files that use the moved symbol."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_usage_file_updates(self, tmpdir) -> None:
        """Test that usage files are updated correctly."""
        # language=typescript
        source_content = """
        export function targetFunction() {
            return "test";
        }
        """

        # language=typescript
        usage_content = """
        import { targetFunction } from './source';
        import { otherFunction } from './source';

        export function consumer() {
            return targetFunction();
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
            "usage.ts": usage_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)
            usage_file = codebase.get_file("usage.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check usage file updates
        assert "import { targetFunction } from './destination'" in usage_file.content
        assert "import { otherFunction } from './source'" in usage_file.content


class TestMoveToFileComplexScenarios:
    """Test complex scenarios with multiple files and dependencies."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_complex_dependency_chain(self, tmpdir) -> None:
        """Test moving a symbol with a complex chain of dependencies."""
        # language=typescript
        source_content = """
        import { helperA } from './helper-a';
        import { helperB } from './helper-b';
        import type { ConfigType } from './types';

        export function targetFunction(config: ConfigType) {
            return helperA(helperB(config));
        }
        """

        # language=typescript
        helper_a_content = """
        import { helperB } from './helper-b';
        export function helperA(value: string) {
            return helperB(value);
        }
        """

        # language=typescript
        helper_b_content = """
        import type { ConfigType } from './types';
        export function helperB(config: ConfigType) {
            return config.value;
        }
        """

        # language=typescript
        types_content = """
        export interface ConfigType {
            value: string;
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
            "helper-a.ts": helper_a_content,
            "helper-b.ts": helper_b_content,
            "types.ts": types_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check imports in destination file
        assert "import { helperA } from './helper-a'" in dest_file.content
        assert "import { helperB } from './helper-b'" in dest_file.content
        assert "import type { ConfigType } from './types'" in dest_file.content

        # Check source file is cleaned up
        assert "helperA" not in source_file.content
        assert "helperB" not in source_file.content
        assert "ConfigType" not in source_file.content


class TestMoveToFileEdgeCases:
    """Test edge cases and error conditions."""

    def test_move_with_self_reference(self, tmpdir) -> None:
        """Test moving a function that references itself."""
        # language=typescript
        source_content = """
        export function targetFunction(n: number): number {
            if (n <= 1) return n;
            return targetFunction(n - 1) + targetFunction(n - 2);
        }
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check self-reference is preserved
        assert "targetFunction(n - 1)" in dest_file.content
        assert "targetFunction(n - 2)" in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_namespace_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses namespace imports."""
        # language=typescript
        source_content = """
        import * as ns1 from './namespace1';
        import * as ns2 from './namespace2';

        export function targetFunction() {
            return ns1.helper(ns2.config);
        }
        """

        # language=typescript
        namespace1_content = """
        export function helper(config: any) {
            return config.value;
        }
        """

        # language=typescript
        namespace2_content = """
        export const config = {
            value: "test"
        };
        """

        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
            "namespace1.ts": namespace1_content,
            "namespace2.ts": namespace2_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check namespace imports are handled correctly
        assert "import * as ns1 from './namespace1'" in dest_file.content
        assert "import * as ns2 from './namespace2'" in dest_file.content
        assert "ns1.helper" in dest_file.content
        assert "ns2.config" in dest_file.content


class TestMoveToFileErrorConditions:
    """Test error conditions and invalid moves."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_circular_dependencies(self, tmpdir) -> None:
        """Test moving a symbol involved in circular dependencies."""
        # language=typescript
        source_content = """
        import { helperB } from './helper-b';

        export function targetFunction() {
            return helperB();
        }
        """

        # language=typescript
        helper_b_content = """
        import { targetFunction } from './source';

        export function helperB() {
            return targetFunction();
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {source_filename: source_content, dest_filename: dest_content, "helper-b.ts": helper_b_content}

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)
            helper_b_file = codebase.get_file("helper-b.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check circular dependency is resolved
        assert "import { targetFunction } from './destination'" in helper_b_file.content
        assert "import { helperB } from './helper-b'" in dest_file.content


class TestMoveToFileJSXScenarios:
    """Test moving JSX/TSX components and related scenarios."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_component_with_props(self, tmpdir) -> None:
        """Test moving a React component with props interface."""
        # language=typescript
        source_content = """
        import React from 'react';
        import type { ButtonProps } from './types';
        import { styled } from '@emotion/styled';

        const StyledButton = styled.button`
            color: blue;
        `;

        export function TargetComponent({ onClick, children }: ButtonProps) {
            return (
                <StyledButton onClick={onClick}>
                    {children}
                </StyledButton>
            );
        }
        """

        source_filename = "source.tsx"
        dest_filename = "destination.tsx"
        # language=typescript
        dest_content = """
        """

        files = {source_filename: source_content, dest_filename: dest_content}

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_component = source_file.get_function("TargetComponent")
            target_component.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check JSX-specific imports and dependencies
        assert "import React from 'react'" in dest_file.content
        assert "import type { ButtonProps } from './types'" in dest_file.content
        assert "import { styled } from '@emotion/styled'" in dest_file.content
        assert "const StyledButton = styled.button" in dest_file.content


class TestMoveToFileModuleAugmentation:
    """Test moving symbols with module augmentation."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_module_augmentation(self, tmpdir) -> None:
        """Test moving a symbol that involves module augmentation."""
        # language=typescript
        source_content = """
        declare module 'external-module' {
            export interface ExternalType {
                newProperty: string;
            }
        }

        import type { ExternalType } from 'external-module';

        export function targetFunction(param: ExternalType) {
            return param.newProperty;
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check module augmentation is handled
        assert "declare module 'external-module'" in dest_file.content
        assert "interface ExternalType" in dest_file.content
        assert "import type { ExternalType }" in dest_file.content


class TestMoveToFileReExportChains:
    """Test moving symbols involved in re-export chains."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_reexport_chain(self, tmpdir) -> None:
        """Test moving a symbol that's re-exported through multiple files."""
        # language=typescript
        source_content = """
        export function targetFunction() {
            return "test";
        }
        """

        # language=typescript
        barrel_a_content = """
        export { targetFunction } from './source';
        """

        # language=typescript
        barrel_b_content = """
        export * from './barrel-a';
        """

        # language=typescript
        usage_content = """
        import { targetFunction } from './barrel-b';

        export function consumer() {
            return targetFunction();
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {source_filename: source_content, dest_filename: dest_content, "barrel-a.ts": barrel_a_content, "barrel-b.ts": barrel_b_content, "usage.ts": usage_content}

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)
            barrel_a_file = codebase.get_file("barrel-a.ts")
            barrel_b_file = codebase.get_file("barrel-b.ts")
            usage_file = codebase.get_file("usage.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check re-export chain updates
        assert "export { targetFunction } from './destination'" in barrel_a_file.content
        assert "export * from './barrel-a'" in barrel_b_file.content
        assert "import { targetFunction } from './barrel-b'" in usage_file.content


class TestMoveToFileAmbientDeclarations:
    """Test moving symbols with ambient declarations."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_ambient_module(self, tmpdir) -> None:
        """Test moving a symbol that uses ambient module declarations."""
        # language=typescript
        source_content = """
        declare module 'config' {
            interface Config {
                apiKey: string;
                endpoint: string;
            }
        }

        import type { Config } from 'config';

        export function targetFunction(config: Config) {
            return fetch(config.endpoint, {
                headers: { 'Authorization': config.apiKey }
            });
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check ambient declarations are moved
        assert "declare module 'config'" in dest_file.content
        assert "interface Config" in dest_file.content
        assert "import type { Config } from 'config'" in dest_file.content


class TestMoveToFileGenerics:
    """Test moving symbols with generic type parameters."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_generic_constraints(self, tmpdir) -> None:
        """Test moving a function with generic type constraints."""
        # language=typescript
        source_content = """
        import { Validator, Serializable } from './types';

        export function targetFunction<T extends Serializable, U extends Validator<T>>(
            value: T,
            validator: U
        ): T {
            return validator.validate(value);
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        assert "import { Validator, Serializable }" not in source_file.content
        assert "import { Validator, Serializable } from './types'" in dest_file.content


class TestMoveToFileDecoratorFactories:
    """Test moving symbols with decorator factories."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_decorator_factories(self, tmpdir) -> None:
        """Test moving a function that uses decorator factories."""
        # language=typescript
        source_content = """
        import { createDecorator } from './decorator-factory';
        import type { Options } from './types';

        const customDecorator = createDecorator<Options>({ timeout: 1000 });

        @customDecorator
        export function targetFunction() {
            return new Promise(resolve => setTimeout(resolve, 1000));
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check decorator factory and its dependencies are moved
        assert "import { createDecorator }" in dest_file.content
        assert "import type { Options }" in dest_file.content
        assert "const customDecorator = createDecorator" in dest_file.content


class TestMoveToFileDefaultExports:
    """Test moving symbols with default exports and re-exports."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_default_export(self, tmpdir) -> None:
        """Test moving a default exported function."""
        # language=typescript
        source_content = """
        import { helper } from './helper';

        export default function targetFunction() {
            return helper();
        }
        """

        # language=typescript
        usage_content = """
        import targetFunction from './source';
        import { default as renamed } from './source';

        export const result = targetFunction();
        export const aliased = renamed();
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {source_filename: source_content, dest_filename: dest_content, "usage.ts": usage_content}

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)
            usage_file = codebase.get_file("usage.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Check default export handling
        assert "import targetFunction from './destination'" in usage_file.content
        assert "import { default as renamed } from './destination'" in usage_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_multiline_imports(self, tmpdir) -> None:
        """Test removing unused imports from multiline import statements"""
        # language=typescript
        source_content = """
        import {
            helperUtil,
            formatUtil,
            parseUtil,
            unusedUtil
        } from './utils';
        import { otherUtil } from './other';

        export function targetFunction() {
            const formatted = formatUtil(helperUtil("test"));
            return parseUtil(formatted);
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Verify only used imports were moved
        assert "unusedUtil" not in source_file.content
        assert "otherUtil" not in source_file.content
        assert "helperUtil" in dest_file.content
        assert "formatUtil" in dest_file.content
        assert "parseUtil" in dest_file.content
        assert "unusedUtil" not in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_aliased_imports(self, tmpdir) -> None:
        """Test removing unused imports with aliases"""
        # language=typescript
        source_content = """
        import { helperUtil as helper } from './utils';
        import { formatUtil as fmt, parseUtil as parse } from './formatters';
        import { validateUtil as validate } from './validators';

        export function targetFunction() {
            return helper(fmt("test"));
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Verify only used aliased imports were moved
        assert "helper" not in source_file.content
        assert "fmt" not in source_file.content
        assert "parse" not in source_file.content
        assert "validate" in source_file.content
        assert "helper" in dest_file.content
        assert "fmt" in dest_file.content
        assert "parse" not in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_back_edge_with_import_retention(self, tmpdir) -> None:
        """Test back edge strategy retains necessary imports"""
        # language=typescript
        source_content = """
        import { helperUtil } from './utils';
        import { otherUtil } from './other';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="add_back_edge", cleanup_unused_imports=True)

        # Source file should have import from new location but keep originals
        assert "import { targetFunction } from './destination'" in source_file.content
        assert "import { helperUtil } from './utils'" in source_file.content
        assert "import { otherUtil } from './other'" in source_file.content
        # Destination should have required imports
        assert "import { helperUtil } from './utils'" in dest_file.content


class TestMoveToFileStrategies:
    """Test different move strategies and their behaviors."""

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_update_all_imports_strategy(self, tmpdir) -> None:
        """Test update_all_imports strategy behavior"""
        # language=typescript
        source_content = """
        import { helperUtil } from './utils';
        import { otherUtil } from './other';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports", cleanup_unused_imports=True)

        assert "import { helperUtil } from './utils'" not in source_file.content
        assert "import { otherUtil } from './other'" not in source_file.content
        assert "import { helperUtil } from './utils'" in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_back_edge_strategy(self, tmpdir) -> None:
        """Test back edge strategy behavior"""
        # language=typescript
        source_content = """
        import { helperUtil } from './utils';
        import { otherUtil } from './other';

        export function targetFunction() {
            return helperUtil("test");
        }
        """

        source_filename = "source.ts"
        dest_filename = "destination.ts"
        # language=typescript
        dest_content = """
        """

        files = {
            source_filename: source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file(source_filename)
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="add_back_edge", cleanup_unused_imports=True)

        # Source file should have import from new location
        assert "import { targetFunction } from './destination'" in source_file.content
        assert "import { helperUtil } from './utils'" in source_file.content
        assert "import { otherUtil } from './other'" in source_file.content
        # Destination should have required imports
        assert "import { helperUtil } from './utils'" in dest_file.content

    def test_move_with_absolute_imports(self, tmpdir) -> None:
        """Test moving a symbol that uses absolute imports"""
        # language=typescript
        source_content = """
        import { helperUtil } from '@/utils/helpers';
        import { formatUtil } from '/src/utils/format';
        import { configUtil } from '~/config';

        export function targetFunction() {
            return helperUtil(formatUtil(configUtil.getValue()));
        }
        """

        dest_filename = "destination.ts"
        dest_content = ""

        files = {
            "source.ts": source_content,
            dest_filename: dest_content,
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("source.ts")
            dest_file = codebase.get_file(dest_filename)

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Verify absolute imports are preserved
        assert "import { helperUtil } from '@/utils/helpers'" in dest_file.content
        assert "import { formatUtil } from '/src/utils/format'" in dest_file.content
        assert "import { configUtil } from '~/config'" in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_complex_relative_paths(self, tmpdir) -> None:
        """Test moving a symbol that uses complex relative paths"""
        # language=typescript
        source_content = """
        import { helperA } from '../../../utils/helpers';
        import { helperB } from '../../../../shared/utils';
        import { helperC } from './local/helper';

        export function targetFunction() {
            return helperA(helperB(helperC()));
        }
        """

        files = {
            "src/features/auth/components/source.ts": source_content,
            "src/features/user/services/destination.ts": "",
            "src/utils/helpers.ts": "export const helperA = (x) => x;",
            "shared/utils.ts": "export const helperB = (x) => x;",
            "src/features/auth/components/local/helper.ts": "export const helperC = () => 'test';",
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("src/features/auth/components/source.ts")
            dest_file = codebase.get_file("src/features/user/services/destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Verify relative paths are correctly updated based on new file location
        assert "import { helperA } from '../../utils/helpers'" in dest_file.content
        assert "import { helperB } from '../../../../shared/utils'" in dest_file.content
        assert "import { helperC } from '../../auth/components/local/helper'" in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_with_mixed_import_styles(self, tmpdir) -> None:
        """Test moving a symbol that uses mixed import styles"""
        # language=typescript
        source_content = """
        import defaultHelper from '@/helpers/default';
        import * as utils from '~/utils';
        import { namedHelper as aliasedHelper } from '../shared/helpers';
        import type { HelperType } from './types';
        const dynamicHelper = await import('./dynamic-helper');

        export function targetFunction(): HelperType {
            return defaultHelper(
                utils.helper(
                    aliasedHelper(
                        dynamicHelper.default()
                    )
                )
            );
        }
        """

        files = {
            "src/features/source.ts": source_content,
            "src/services/destination.ts": "",
            "src/helpers/default.ts": "export default (x) => x;",
            "lib/utils.ts": "export const helper = (x) => x;",
            "src/shared/helpers.ts": "export const namedHelper = (x) => x;",
            "src/features/types.ts": "export type HelperType = string;",
            "src/features/dynamic-helper.ts": "export default () => 'test';",
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("src/features/source.ts")
            dest_file = codebase.get_file("src/services/destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Verify different import styles are handled correctly
        assert "import defaultHelper from '@/helpers/default'" in dest_file.content
        assert "import * as utils from '~/utils'" in dest_file.content
        assert "import { namedHelper as aliasedHelper } from '../shared/helpers'" in dest_file.content
        assert "import type { HelperType } from '../features/types'" in dest_file.content
        assert "const dynamicHelper = await import('../features/dynamic-helper')" in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_between_monorepo_packages(self, tmpdir) -> None:
        """Test moving a symbol between different packages in a monorepo"""
        # language=typescript
        source_content = """
        import { sharedUtil } from '@myorg/shared';
        import { helperUtil } from '@myorg/utils';
        import { localUtil } from './utils';

        export function targetFunction() {
            return sharedUtil(helperUtil(localUtil()));
        }
        """

        files = {
            "packages/package-a/src/source.ts": source_content,
            "packages/package-b/src/destination.ts": "",
            "packages/shared/src/index.ts": "export const sharedUtil = (x) => x;",
            "packages/utils/src/index.ts": "export const helperUtil = (x) => x;",
            "packages/package-a/src/utils.ts": "export const localUtil = () => 'test';",
            "packages/package-a/package.json": '{"name": "@myorg/package-a"}',
            "packages/package-b/package.json": '{"name": "@myorg/package-b"}',
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("packages/package-a/src/source.ts")
            dest_file = codebase.get_file("packages/package-b/src/destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Verify package imports are handled correctly
        assert "import { sharedUtil } from '@myorg/shared'" in dest_file.content
        assert "import { helperUtil } from '@myorg/utils'" in dest_file.content
        assert "import { localUtil } from '@myorg/package-a/src/utils'" in dest_file.content

    @pytest.mark.skip(reason="This test or related implementation needs work.")
    def test_move_between_different_depths(self, tmpdir) -> None:
        """Test moving a symbol between files at different directory depths"""
        # language=typescript
        source_content = """
        import { helperA } from './helper';
        import { helperB } from '../utils/helper';
        import { helperC } from '../../shared/helper';

        export function targetFunction() {
            return helperA(helperB(helperC()));
        }
        """

        files = {
            "src/features/auth/source.ts": source_content,
            "src/features/auth/helper.ts": "export const helperA = (x) => x;",
            "src/features/utils/helper.ts": "export const helperB = (x) => x;",
            "src/shared/helper.ts": "export const helperC = () => 'test';",
            "lib/services/destination.ts": "",
        }

        with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files=files) as codebase:
            source_file = codebase.get_file("src/features/auth/source.ts")
            dest_file = codebase.get_file("lib/services/destination.ts")

            target_function = source_file.get_function("targetFunction")
            target_function.move_to_file(dest_file, include_dependencies=True, strategy="update_all_imports")

        # Verify imports are updated for new directory depth
        assert "import { helperA } from '../../src/features/auth/helper'" in dest_file.content
        assert "import { helperB } from '../../src/features/utils/helper'" in dest_file.content
        assert "import { helperC } from '../../src/shared/helper'" in dest_file.content


class TestMoveToFileFileSystem:
    """Test moving functions with different file system considerations."""

    @pytest.mark.skipif(condition=platform.system() != "Linux", reason="Only works on case-sensitive file systems")
    def test_function_move_to_file_lower_upper(self, tmpdir) -> None:
        # language=typescript
        content1 = """
export function foo(): number {
    return bar() + 1;
}

export function bar(): number {
    return foo() + 1;
}
        """
        with get_codebase_session(tmpdir, files={"file1.ts": content1}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
            file1 = codebase.get_file("file1.ts")
            foo = file1.get_function("foo")
            bar = file1.get_function("bar")
            assert bar in foo.dependencies
            assert foo in bar.dependencies

            file2 = codebase.create_file("File1.ts", "")
            foo.move_to_file(file2, include_dependencies=True, strategy="add_back_edge")

        # language=typescript
        assert (
            file2.content.strip()
            == """
export function bar(): number {
    return foo() + 1;
}

export function foo(): number {
    return bar() + 1;
}
    """.strip()
        )
        assert file1.content.strip() == "export { bar } from 'File1'\nexport { foo } from 'File1'"

    @pytest.mark.skipif(condition=platform.system() != "Linux", reason="Only works on case-sensitive file systems")
    def test_function_move_to_file_lower_upper_no_deps(self, tmpdir) -> None:
        # language=typescript
        content1 = """
export function foo(): number {
    return bar() + 1;
}

export function bar(): number {
    return foo() + 1;
}
        """
        with get_codebase_session(tmpdir, files={"file1.ts": content1}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
            file1 = codebase.get_file("file1.ts")
            foo = file1.get_function("foo")
            bar = file1.get_function("bar")
            assert bar in foo.dependencies
            assert foo in bar.dependencies

            file2 = codebase.create_file("File1.ts", "")
            foo.move_to_file(file2, include_dependencies=False, strategy="add_back_edge")

        # language=typescript
        assert (
            file1.content.strip()
            == """export { foo } from 'File1';

export function bar(): number {
    return foo() + 1;
}"""
        )
        # language=typescript
        assert (
            file2.content.strip()
            == """
import { bar } from 'file1';


export function foo(): number {
    return bar() + 1;
}
    """.strip()
        )
