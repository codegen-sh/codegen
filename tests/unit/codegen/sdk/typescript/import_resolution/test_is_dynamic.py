from codegen.sdk.codebase.factory.get_session import get_codebase_session
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
            const module = await import('./lazy');
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


def test_ts_import_is_dynamic_in_do_statement(tmpdir):
    # language=typescript
    content = """
    import { shouldContinue } from './utils';

    do {
        const module = await import('./dynamic-module');
        module.process();
    } while (shouldContinue());
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in do-while loop


def test_ts_import_is_dynamic_in_switch_statement(tmpdir):
    # language=typescript
    content = """
    import { getFeatureFlag } from './utils';

    switch (getFeatureFlag()) {
        case 'feature1':
            import('./feature1').then(module => {
                module.init();
            });
            break;
        case 'feature2':
            import('./feature2').then(module => {
                module.init();
            });
            break;
        default:
            import('./default').then(module => {
                module.init();
            });
    }
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        imports = file.imports

        assert not imports[0].is_dynamic  # static import
        assert imports[1].is_dynamic  # dynamic import in first case
        assert imports[2].is_dynamic  # dynamic import in second case
        assert imports[3].is_dynamic  # dynamic import in default case
