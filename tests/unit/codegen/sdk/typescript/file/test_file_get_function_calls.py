from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_file_get_function_calls(tmpdir) -> None:
    # language=typescript
    content = """
import { Logger } from 'some-logging-library'; // Assuming a Logger type is available

function getLogger(name: string): Logger {
    return new Logger(name);
}

const errorLogger = getLogger(__filename).error();

class MyClass {
    constructor() {
        nestedFunctionCall().chained().calls();
    }
}

function topLevelFunction(): void {
    bar();
}
"""
    with get_codebase_session(tmpdir=tmpdir, files={"file.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("file.ts")
        function_calls = file.function_calls
        assert len(function_calls) == 7
        # "Logger" should be a function call (CG-8625)
        assert set([fcall.name for fcall in function_calls]) == {"Logger", "getLogger", "error", "nestedFunctionCall", "chained", "calls", "bar"}

        my_class = codebase.get_symbol("MyClass")
        class_fcalls = my_class.function_calls
        assert len(class_fcalls) == 3
        assert set([fcall.name for fcall in class_fcalls]) == {"nestedFunctionCall", "chained", "calls"}

        top_level = codebase.get_symbol("topLevelFunction")
        function_fcalls = top_level.function_calls
        assert len(function_fcalls) == 1
        assert set([fcall.name for fcall in function_fcalls]) == {"bar"}
