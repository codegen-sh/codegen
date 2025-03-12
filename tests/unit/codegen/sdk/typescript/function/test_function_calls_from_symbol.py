import pytest

from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.detached_symbols.argument import Argument
from codegen.sdk.core.expressions.binary_expression import BinaryExpression
from codegen.sdk.core.expressions.parenthesized_expression import ParenthesizedExpression
from codegen.sdk.core.statements.expression_statement import ExpressionStatement
from codegen.sdk.core.statements.return_statement import ReturnStatement
from codegen.sdk.core.statements.statement import StatementType
from codegen.sdk.typescript.detached_symbols.decorator import TSDecorator
from codegen.sdk.typescript.expressions.chained_attribute import TSChainedAttribute
from codegen.sdk.typescript.statements.assignment_statement import TSAssignmentStatement
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_calls_from_file(tmpdir):
    # language=typescript
    content = """
import { x, y, z } from './some_file';

function foo(): number {
    return bar();
}

function bar(): number {
    function random(): number {
        return Math.floor(Math.random() * 101);
    }
    return random();
}

(function main() {
    console.log(foo());
    console.log(bar());
})();
    """
    # language=typescript
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.function_calls
        main_call = """(function main() {
    console.log(foo());
    console.log(bar());
})"""

        assert set(f.name for f in fcalls) == {"foo", "bar", "floor", "random", "log", main_call}
        assert len(fcalls) == 9
        fcall_parents = [(f.name, type(f.parent), f.parent.source) for f in file.function_calls]
        assert fcall_parents == [
            ("bar", ReturnStatement, "return bar();"),
            ("floor", ReturnStatement, "return Math.floor(Math.random() * 101);"),
            ("random", BinaryExpression, "Math.random() * 101"),
            ("random", ReturnStatement, "return random();"),
            (main_call, ExpressionStatement, f"{main_call}();"),
            ("log", ExpressionStatement, "console.log(foo());"),
            ("foo", Argument, "foo()"),
            ("log", ExpressionStatement, "console.log(bar());"),
            ("bar", Argument, "bar()"),
        ]


def test_function_calls_from_class(tmpdir):
    # language=typescript
    content = """
import { bar } from './some_file';

class A {
    _attr = bar();

    constructor() {
        this._attr = this.foo();
    }

    foo(): ReturnType<typeof bar> {
        return bar();
    }
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.get_class("A").function_calls

        assert set(f.name for f in fcalls) == {"bar", "foo"}
        assert len(fcalls) == 3
        fcall_parent_1 = file.function_calls[0]
        fcall_parent_2 = file.function_calls[1]
        fcall_parent_3 = file.function_calls[2]

        assert fcall_parent_1.parent.parent.parent.level == 1
        assert fcall_parent_1.name == "bar"
        assert fcall_parent_1.parent.parent.statement_type == StatementType.CLASS_ATTRIBUTE

        assert fcall_parent_2.parent.parent.parent.level == 2
        assert fcall_parent_2.name == "foo"
        assert fcall_parent_2.parent.parent.statement_type == StatementType.ASSIGNMENT

        assert fcall_parent_3.parent.parent.level == 2
        assert fcall_parent_3.name == "bar"
        assert fcall_parent_3.parent.statement_type == StatementType.RETURN_STATEMENT


@pytest.mark.skip(reason="CG-9422 TS method decorator parsing needs to be fixed first")
def test_function_calls_from_decorated_definitions(tmpdir):
    # language=typescript
    content = """
import { describe, it } from 'jest';
import { myDecorator, myDecorator2 } from './decorators';
import { d } from './some_file';

@myDecorator()
@myDecorator2({ a: 1, b: 2, c: d() })
class A {

    constructor() {
        this._attr = this.foo();
    }

    @methodDecorator()
    decoratedMethod(x: number, y: string): string {
        return `x: ${x}, y: ${y}`;
    }
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.get_class("A").function_calls

        assert set(f.name for f in fcalls) == {"myDecorator", "myDecorator2", "d", "foo", "methodDecorator"}
        assert len(fcalls) == 6

        fcall_parents = [(f.name, type(f.parent)) for f in fcalls]
        assert fcall_parents == [
            ("myDecorator", TSDecorator),
            ("myDecorator2", TSDecorator),
            ("d", TSDecorator),
            ("foo", TSAssignmentStatement),
            ("methodDecorator", TSDecorator),
        ]


@pytest.mark.xfail(reason="Broken by function call changes")
def test_function_calls_from_datatypes(tmpdir):
    # language=typescript
    content = """
function getConfig(): { max_retries: number; timeout: number } {
    // object dictionary
    const config = {
        max_retries: getMaxRetries(),
        timeout: calculateTimeout()
    };
    return config;
}

// array
const data: [number, number, number] = [getX(), getY(), getZ()];

// arrow function
const transformed = data.map(x => transform(x));
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.function_calls

        assert set(f.name for f in fcalls) == {"getMaxRetries", "calculateTimeout", "getX", "getY", "getZ", "map", "transform"}
        assert len(fcalls) == 7
        fcall_parents = [(f.parent.parent.level, f.name, f.parent.statement_type) for f in fcalls]
        assert fcall_parents == [
            # dictionary
            (1, "getMaxRetries", StatementType.ASSIGNMENT),
            (1, "calculateTimeout", StatementType.ASSIGNMENT),
            # array
            (0, "getX", StatementType.ASSIGNMENT),
            (0, "getY", StatementType.ASSIGNMENT),
            (0, "getZ", StatementType.ASSIGNMENT),
            # arrow function
            (0, "map", StatementType.ASSIGNMENT),
            (0, "transform", StatementType.ASSIGNMENT),
        ]


def test_function_calls_from_function_parameters(tmpdir):
    # language=typescript
    content = """
// function parameters
function greet(name: string = getDefaultName()): void {
    console.log(`Hello, ${name}!`);
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.function_calls
        func = file.get_function("greet")

        assert set(f.name for f in fcalls) == {"getDefaultName", "log"}
        assert len(fcalls) == 2
        fcall_parents = [(f.name, f.parent) for f in file.function_calls]
        assert fcall_parents == [
            ("getDefaultName", func.parameters[0]),
            ("log", func.code_block.statements[0]),
        ]


def test_function_calls_from_while_loop(tmpdir):
    # language=typescript
    content = """
// while loop conditions
while (hasNextItem()) {
    processItem();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.function_calls

        assert set(f.name for f in fcalls) == {"hasNextItem", "processItem"}
        assert len(fcalls) == 2
        assert file.function_calls[0].parent.parent.parent.level == 0
        assert file.function_calls[0].name == "hasNextItem"
        assert file.function_calls[0].parent.parent.statement_type == StatementType.WHILE_STATEMENT
        assert file.function_calls[1].parent.parent.level == 1
        assert file.function_calls[1].name == "processItem"
        assert file.function_calls[1].parent.statement_type == StatementType.EXPRESSION_STATEMENT


def test_function_calls_from_if_conditions(tmpdir):
    # language=typescript
    content = """
// if conditions
if (isValid(userInput)) {
    processData();
} else if (isInvalid(userInput)) {
    handleError();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.function_calls

        assert set(f.name for f in fcalls) == {"isValid", "processData", "isInvalid", "handleError"}
        assert len(fcalls) == 4
        fcall_parents = [(f.name, type(f.parent)) for f in file.function_calls]
        assert fcall_parents == [
            ("isValid", ParenthesizedExpression),
            ("processData", ExpressionStatement),
            ("isInvalid", ParenthesizedExpression),
            ("handleError", ExpressionStatement),
        ]


def test_function_calls_for_nested_calls(tmpdir):
    # language=typescript
    content = """
parent(nested())
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.function_calls

        assert set(f.name for f in fcalls) == {"parent", "nested"}
        assert len(fcalls) == 2
        fcall_parents = [(f.name, type(f.parent)) for f in fcalls]
        assert fcall_parents == [
            ("parent", ExpressionStatement),
            ("nested", Argument),
        ]


def test_function_calls_for_chained_calls(tmpdir):
    # language=typescript
    content = """
parent().child().grandchild()
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.function_calls

        assert set(f.name for f in fcalls) == {"parent", "child", "grandchild"}
        assert len(fcalls) == 3
        fcall_parents = [(f.name, type(f.parent)) for f in fcalls]
        assert fcall_parents == [
            ("grandchild", ExpressionStatement),
            ("child", TSChainedAttribute),
            ("parent", TSChainedAttribute),
        ]
        assert fcalls[0].parent == file.code_block.statements[0]
        assert fcalls[1].parent.parent == fcalls[0]
        assert fcalls[2].parent.parent == fcalls[1]


def test_function_calls_in_function_call(tmpdir):
    # language=typescript
    content = """
describe("top level", () => {
    const numVal = 1;
    describe("#roundToNearestOrderOfMagnitude", () => {
      it("should round to the nearest order of magnitude", () => {
        expect(roundToNearestOrderOfMagnitude(0)).toBe(numVal)
        expect(roundToNearestOrderOfMagnitude(1)).toBe(10)
      })

      it("should work for negative numbers", () => {
        expect(roundToNearestOrderOfMagnitude(-1)).toBe(1)
      })
    })
})
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        fcalls = file.function_calls

        assert set(f.name for f in fcalls) == {"describe", "it", "roundToNearestOrderOfMagnitude", "expect", "toBe"}
        assert len(fcalls) == 13
        fcall_parents = [(f.name, type(f.parent)) for f in fcalls]
        assert fcall_parents == [
            ("describe", ExpressionStatement),
            ("describe", ExpressionStatement),
            ("it", ExpressionStatement),
            ("toBe", ExpressionStatement),
            ("expect", TSChainedAttribute),
            ("roundToNearestOrderOfMagnitude", Argument),
            ("toBe", ExpressionStatement),
            ("expect", TSChainedAttribute),
            ("roundToNearestOrderOfMagnitude", Argument),
            ("it", ExpressionStatement),
            ("toBe", ExpressionStatement),
            ("expect", TSChainedAttribute),
            ("roundToNearestOrderOfMagnitude", Argument),
        ]
