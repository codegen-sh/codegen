from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_decorators_get_multiple_decorators(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Foo {
    @thing1
    @thing2(1, '2', a=3)
    @thing3.abc
    @thing4.xyz(1, '2', a=3)
    doSomething() {
        // Simulating a time-consuming operation
        for (let i = 0; i < 1000000; i++) {
            // Do something
        }
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        foo = codebase.get_symbol("Foo")
        do_something = foo.get_method("doSomething")
        do_something_decorators = do_something.decorators

        assert len(do_something_decorators) == 4
        assert do_something_decorators[3].source == "@thing1"
        assert do_something_decorators[2].source == "@thing2(1, '2', a=3)"
        assert do_something_decorators[1].source == "@thing3.abc"
        assert do_something_decorators[0].source == "@thing4.xyz(1, '2', a=3)"


def test_function_decorators_multiple_methods(tmpdir) -> None:
    FILENAME = "test.ts"
    # language=typescript
    FILE_CONTENT = """
class Foo {
    @dec1(1, '2', a=3)
    @dec2
    doSomething1() {
        // Simulating a time-consuming operation
        for (let i = 0; i < 1000000; i++) {
            // Do something
        }
    }

    @dec3
    doSomething2(){
        console.log("do something 2")
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={FILENAME: FILE_CONTENT}) as codebase:
        foo = codebase.get_symbol("Foo")
        do_something_1 = foo.get_method("doSomething1")
        do_something_1_decorators = do_something_1.decorators
        assert len(do_something_1_decorators) == 2
        assert do_something_1_decorators[0].source == "@dec2"
        assert do_something_1_decorators[1].source == "@dec1(1, '2', a=3)"

        do_something_2 = foo.get_method("doSomething2")
        do_something_2_decorators = do_something_2.decorators
        assert len(do_something_2_decorators) == 1
        assert do_something_2_decorators[0].source == "@dec3"
