from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.sdk.core.statements.statement import StatementType
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_switch_statement_parse(tmpdir) -> None:
    # language=typescript
    content = """
switch (x) {
    case 1:
        doSomething();
        break;
    case 2:
        doSomethingElse();
        break;
    default:
        doDefault();
}
switch (y) {
    case "a":
        handleA();
        break;
    case "b":
        handleB();
        break;
    default:
        handleDefault();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        statements = file.code_block.statements
        switch_1 = statements[0]
        switch_2 = statements[1]
        assert switch_1.statement_type == StatementType.SWITCH_STATEMENT
        assert switch_2.statement_type == StatementType.SWITCH_STATEMENT
        assert len(switch_1.cases) == 3
        assert len(switch_2.cases) == 3
        assert switch_1.cases[0].condition.source == "1"
        assert switch_1.cases[1].condition.source == "2"
        assert switch_1.cases[2].default is True
        assert switch_2.cases[0].condition.source == '"a"'
        assert switch_2.cases[1].condition.source == '"b"'
        assert switch_2.cases[2].default is True


def test_switch_statement_function_calls(tmpdir) -> None:
    # language=typescript
    content = """
switch (fruit) {
    case "apple":
        eatApple();
        break;
    case "banana":
        eatBanana();
        break;
    default:
        eatFruit();
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        switch = file.code_block.statements[0]
        assert len(switch.function_calls) == 3
        assert switch.function_calls[0].source == "eatApple()"
        assert switch.function_calls[1].source == "eatBanana()"
        assert switch.function_calls[2].source == "eatFruit()"


def test_switch_statement_dependencies(tmpdir) -> None:
    # language=typescript
    content = """
var fruit = "apple";
function selectFruit() {
    switch (fruit) {
        case "apple":
            processApple();
            break;
        case "orange":
            processOrange();
            break;
        default:
            processOtherFruit();
    }
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        selectFruit = file.get_function("selectFruit")
        assert len(selectFruit.dependencies) == 1
        assert selectFruit.dependencies[0] == file.get_global_var("fruit")
