from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_decorator_call_should_find_expression(tmpdir) -> None:
    content = """
function decorator(param: string) {
  return function (target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    descriptor.value = function (...args: any[]) {
      return originalMethod.apply(this, args);
    };
    return descriptor;
  };
}

class TestClass {
  @decorator('test param')
  testMethod(arg1: string, arg2: number) {
    // Method implementation
  }
}
"""
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"decorator.ts": content}) as ctx:
        file = ctx.get_file("decorator.ts")
        test_class = file.get_class("TestClass")
        test_method = test_class.get_method("testMethod")

        # Verify decorator exists
        assert len(test_method.decorators) == 1
        test_decorator = test_method.decorators[0]
        assert test_decorator.call

        # Verify decorator call details
        decorator_call = test_decorator.call
        assert decorator_call.name == "decorator"
        assert len(decorator_call.args) == 1
        assert decorator_call.args[0].value == "'test param'"
