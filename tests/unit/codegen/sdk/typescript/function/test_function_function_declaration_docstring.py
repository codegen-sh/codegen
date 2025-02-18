from codegen.sdk.codebase.factory.get_session import get_codebase_graph_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_signature(tmpdir) -> None:
    content = """
function add(a: number, b: number): number {
  return a + b;
}

const multiply = function(a: number, b: number): number {
  return a * b;
};

const subtract = (a: number, b: number): number => {
  return a - b;
};

const divide = (a: number, b: number) => a / b;

function greet(name: string, greeting?: string): string {
  return `${greeting || 'Hello'}, ${name}!`;
}

function* numberGenerator(start: number, end: number): IterableIterator<number> {
  for (let i = start; i <= end; i++) {
    yield i;
  }
}
"""
    # =====[ Dependencies ]=====
    with get_codebase_graph_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": content}) as ctx:
        file = ctx.get_file("test.ts")
        add_function = file.get_function("add")
        func_dec_str = add_function.function_signature
        assert func_dec_str == "function add(a: number, b: number): number"

        mult_function = file.get_function("multiply")
        mult_dec_str = mult_function.function_signature
        assert mult_dec_str == "multiply = function(a: number, b: number): number"

        subtract_function = file.get_function("subtract")
        subtract_dec_str = subtract_function.function_signature
        assert subtract_dec_str == "subtract = (a: number, b: number): number"

        divide_function = file.get_function("divide")
        divide_dec_str = divide_function.function_signature
        assert divide_dec_str == "divide = (a: number, b: number)"

        greet_function = file.get_function("greet")
        greet_dec_str = greet_function.function_signature
        assert greet_dec_str == "function greet(name: string, greeting?: string): string"

        number_generator = file.get_function("numberGenerator")
        number_dec_str = number_generator.function_signature
        assert number_dec_str == "function* numberGenerator(start: number, end: number): IterableIterator<number>"
