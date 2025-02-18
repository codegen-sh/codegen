from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_decorator_name_returns_source(tmpdir) -> None:
    content = """
function measure(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;

    descriptor.value = function(...args: any[]) {
        const start = performance.now();
        const result = originalMethod.apply(this, args);
        const end = performance.now();
        console.log(`Execution time of ${propertyKey}: ${end - start} ms`);
        return result;
    };

    return descriptor;
}

class PerformanceTest {
    @measure
    doSomething() {
        // Simulating a time-consuming operation
        for (let i = 0; i < 1000000; i++) {
            // Do something
        }
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"decorator.ts": content}) as codebase:
        file = codebase.get_file("decorator.ts")
        performance_test_class = file.get_class("PerformanceTest")
        do_something_method = performance_test_class.get_method("doSomething")
        assert len(do_something_method.decorators) == 1
        measure_decorator = do_something_method.decorators[0]
        assert measure_decorator.name == "measure"


def test_decorator_dotted_name(tmpdir) -> None:
    content = """
class PerformanceTest {
    @measure.performance
    doSomething() {
        // Simulating a time-consuming operation
        for (let i = 0; i < 1000000; i++) {
            // Do something
        }
    }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"decorator.ts": content}) as codebase:
        file = codebase.get_file("decorator.ts")
        performance_test_class = file.get_class("PerformanceTest")
        do_something_method = performance_test_class.get_method("doSomething")
        assert len(do_something_method.decorators) == 1
        measure_decorator = do_something_method.decorators[0]
        assert measure_decorator.full_name == "measure.performance"


def test_decorator_name_function_call(tmpdir) -> None:
    content = """
class PerformanceTest {
    @measure.performance.do(a=1, b=2)
    doSomething() {
        // Simulating a time-consuming operation
        for (let i = 0; i < 1000000; i++) {
            // Do something
        }
    }
}
    """
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"decorator.ts": content}) as codebase:
        file = codebase.get_file("decorator.ts")
        performance_test_class = file.get_class("PerformanceTest")
        do_something_method = performance_test_class.get_method("doSomething")
        assert len(do_something_method.decorators) == 1
        measure_decorator = do_something_method.decorators[0]
        assert measure_decorator.full_name == "measure.performance.do"
