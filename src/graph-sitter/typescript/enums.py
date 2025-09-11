from enum import StrEnum


class TSFunctionTypeNames(StrEnum):
    # const a = function functionExpression(): void {
    #     console.log("This is a regular function expression");
    # };
    FunctionExpression = "function_expression"

    # let arrowFunction = (x,y) => { x + y };
    ArrowFunction = "arrow_function"

    # function* generatorFunctionDeclaration(): Generator<number> {
    #     yield 1;
    # }
    GeneratorFunctionDeclaration = "generator_function_declaration"

    # const a = function* generatorFunction(): Generator<number> {
    #     yield 1;
    # };
    GeneratorFunction = "generator_function"

    # function functionDeclaration(name: string): string {
    #     return `Hello, ${name}!`;
    # }
    FunctionDeclaration = "function_declaration"

    # class Example {
    #   methodDefinition(): void {
    #     console.log("This is a method definition");
    #   }
    # }
    MethodDefinition = "method_definition"

    # Decorated methods (assuming decorators are supported in your JavaScript/TypeScript parser)
    DecoratedMethodDefinition = "decorated_method_definition"
