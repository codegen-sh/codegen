from codegen import Codebase
from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.function import Function
from codegen.sdk.core.statements.for_loop_statement import ForLoopStatement
from codegen.sdk.core.statements.if_block_statement import IfBlockStatement
from codegen.sdk.core.statements.try_catch_statement import TryCatchStatement
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_ts_import_is_dynamic_in_function_declaration(tmpdir):
    # language=typescript
    content = """
    import { staticImport } from './static';

    function loadModule() {
        import('./dynamic').then(module => {
            console.log(module);
        });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in function


def test_ts_import_is_dynamic_in_method_definition(tmpdir):
    # language=typescript
    content = """
    import { Component } from '@angular/core';

    class MyComponent {
        async loadFeature() {
            const feature = await import('./feature');
        }

        @Decorator()
        async decoratedMethod() {
            const module = await import('./decorated');
        }

    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in method
        assert imports[2].is_dynamic  # dynamic import in decorated method


def test_ts_import_is_dynamic_in_arrow_function(tmpdir):
    # language=typescript
    content = """
    import { useState } from 'react';

    const MyComponent = () => {
        const loadModule = async () => {
            const module = await import('./lazy').then((module) => {
                return module.default;
            });
        };

        return <button onClick={loadModule} />;
    };
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in async arrow function


def test_ts_import_is_dynamic_in_if_statement(tmpdir):
    # language=typescript
    content = """
    import { isFeatureEnabled } from './utils';

    if (isFeatureEnabled('feature')) {
        import('./feature').then(module => {
            module.enableFeature();
        });
    } else {
        import('./fallback').then(module => {
            module.useFallback();
        });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in if block
        assert imports[2].is_dynamic  # dynamic import in else block


def test_ts_import_is_dynamic_in_try_statement(tmpdir):
    # language=typescript
    content = """
    import { logger } from './logger';

    try {
        const module = await import('./main');
    } catch (error) {
        const fallback = "hello"
    } finally {
        const cleanup = "hello"
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in try block


def test_ts_import_is_dynamic_in_catch_clause(tmpdir):
    # language=typescript
    content = """
    import { logger } from './logger';

    try {
        const x = 1;
    } catch (error) {
        const errorHandler = await import('./error-handler');
        errorHandler.handle(error);
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in catch block


def test_ts_import_is_dynamic_in_finally_clause(tmpdir):
    # language=typescript
    content = """
    import { logger } from './logger';

    try {
        const x = 1;
    } catch (error) {
        throw error;
    } finally {
        const cleanup = await import('./cleanup');
        cleanup.perform();
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in finally block


def test_ts_import_is_dynamic_in_while_statement(tmpdir):
    # language=typescript
    content = """
    import { condition } from './utils';

    while (condition()) {
        const processor = await import('./processor');
        processor.process();
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in while loop


def test_ts_import_is_dynamic_in_for_statement(tmpdir):
    # language=typescript
    content = """
    import { items } from './data';

    for (let i = 0; i < items.length; i++) {
        const processor = await import('./processor');
        processor.process(items[i]);
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in for loop


def test_parent_of_types_function():
    codebase = Codebase.from_string(
        """
        function hello() {
            import { foo } from 'bar';
        }
        """,
        language="typescript",
    )
    import_stmt = codebase.files[0].imports[0]
    assert import_stmt.parent_of_types({Function}) is not None
    assert import_stmt.parent_of_types({IfBlockStatement}) is None


def test_parent_of_types_if_statement():
    codebase = Codebase.from_string(
        """
        if (true) {
            import { foo } from 'bar';
        }
        """,
        language="typescript",
    )
    import_stmt = codebase.files[0].imports[0]
    assert import_stmt.parent_of_types({IfBlockStatement}) is not None
    assert import_stmt.parent_of_types({Function}) is None


def test_parent_of_types_multiple():
    codebase = Codebase.from_string(
        """
        function hello() {
            if (true) {
                import { foo } from 'bar';
            }
        }
        """,
        language="typescript",
    )
    import_stmt = codebase.files[0].imports[0]
    # Should find both Function and IfBlockStatement parents
    assert import_stmt.parent_of_types({Function, IfBlockStatement}) is not None
    # Should find closest parent first (IfBlockStatement)
    assert isinstance(import_stmt.parent_of_types({Function, IfBlockStatement}), IfBlockStatement)


def test_parent_of_types_try_catch():
    codebase = Codebase.from_string(
        """
        try {
            import { foo } from 'bar';
        } catch (e) {}
        """,
        language="typescript",
    )
    import_stmt = codebase.files[0].imports[0]
    assert import_stmt.parent_of_types({TryCatchStatement}) is not None


def test_parent_of_types_for_loop():
    codebase = Codebase.from_string(
        """
        for (let i = 0; i < 10; i++) {
            import { foo } from 'bar';
        }
        """,
        language="typescript",
    )
    import_stmt = codebase.files[0].imports[0]
    assert import_stmt.parent_of_types({ForLoopStatement}) is not None
