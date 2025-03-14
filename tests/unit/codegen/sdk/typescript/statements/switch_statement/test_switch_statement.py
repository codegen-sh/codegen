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


def test_switch_reassignment_handling(tmpdir) -> None:
    # language=typescript
    content = """
const filter = 1;
switch (filter) {
    case 1:
        PYSPARK = true;
        break;
    case 2:
        PYSPARK = false;
        break;
    default:
        PYSPARK = null;
        break;
}

console.log(PYSPARK);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        symbol = file.get_symbol("PYSPARK")
        func_call = file.function_calls[0]
        pyspark_arg = func_call.args.children[0]
        for symb in file.symbols[1:]:  # Skip the first symbol which is 'filter'
            usage = symb.usages[0]
            assert usage.match == pyspark_arg


def test_switch_reassignment_handling_function(tmpdir) -> None:
    # language=typescript
    content = """
const type = "handler";
switch (type) {
    case "handler":
        function process(){ return "handler"; }
        break;
    case "processor":
        function process(){ return "processor"; }
        break;
    default:
        function process(){ return "default"; }
        break;
}
process();
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        process = file.get_function("process")
        func_call = file.function_calls[0]
        for func in file.functions:
            if func.name == "process":
                usage = func.usages[0]
                assert usage.match == func_call


def test_switch_reassignment_handling_inside_func(tmpdir) -> None:
    # language=typescript
    content = """
function getStatus(code) {
    let status;
    switch (code) {
        case 200:
            status = "OK";
            break;
        case 404:
            status = "Not Found";
            break;
        default:
            status = "Unknown";
            break;
    }
    return status;
}
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        get_status = file.get_function("getStatus")
        return_stmt = get_status.code_block.statements[-1]
        status_var = return_stmt.value
        for symb in file.symbols(True):
            if symb.name == "status":
                assert len(symb.usages) > 0
                assert any(usage.match == status_var for usage in symb.usages)


def test_switch_reassignment_handling_nested(tmpdir) -> None:
    # language=typescript
    content = """
const outer = 1;
switch (outer) {
    case 1:
        RESULT = "outer 1";
        const inner = 2;
        switch (inner) {
            case 2:
                RESULT = "inner 2";
                break;
            default:
                RESULT = "inner default";
                break;
        }
        break;
    default:
        RESULT = "outer default";
        break;
}
console.log(RESULT);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls[0]
        result_arg = func_call.args.children[0]
        for symb in file.symbols:
            if symb.name == "RESULT":
                usage = symb.usages[0]
                assert usage.match == result_arg


def test_switch_multiple_reassignment(tmpdir) -> None:
    # language=typescript
    content = """
const first = 1;
switch (first) {
    case 1:
        VALUE = "first 1";
        break;
    default:
        VALUE = "first default";
        break;
}

const second = 2;
switch (second) {
    case 2:
        VALUE = "second 2";
        break;
    default:
        VALUE = "second default";
        break;
}

console.log(VALUE);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls[0]
        value_arg = func_call.args.children[0]
        for symb in file.symbols:
            if symb.name == "VALUE":
                usage = symb.usages[0]
                assert usage.match == value_arg


def test_switch_fallthrough_reassignment(tmpdir) -> None:
    # language=typescript
    content = """
const code = 1;
switch (code) {
    case 1:
        STATUS = "Processing";
        // Fallthrough intentional
    case 2:
        STATUS = "Almost done";
        // Fallthrough intentional
    case 3:
        STATUS = "Complete";
        break;
    default:
        STATUS = "Unknown";
        break;
}
console.log(STATUS);
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls[0]
        status_arg = func_call.args.children[0]
        for symb in file.symbols:
            if symb.name == "STATUS":
                usage = symb.usages[0]
                assert usage.match == status_arg
