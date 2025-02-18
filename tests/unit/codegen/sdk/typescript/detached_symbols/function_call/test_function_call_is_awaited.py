from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_call_is_awaited_basic(tmpdir) -> None:
    # language=typescript
    file = """
if (a) {
    return await b();
}
c();
await d();
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert len(file.function_calls) == 3

        # Check if the function calls are awaited
        assert file.function_calls[0].is_awaited
        assert not file.function_calls[1].is_awaited
        assert file.function_calls[2].is_awaited


def test_function_call_is_awaited_wrapped(tmpdir) -> None:
    # language=typescript
    file = """
if (a) {
    return await (b());
}
c();
(d());
await (((e())));
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert len(file.function_calls) == 4

        # Check if the function calls are awaited
        assert file.function_calls[0].is_awaited
        assert not file.function_calls[1].is_awaited
        assert not file.function_calls[2].is_awaited
        assert file.function_calls[3].is_awaited


def test_function_call_is_awaited_nested(tmpdir) -> None:
    # language=typescript
    file = """
await doSomething(() => {
  doAsync() // this is unawaited
})
"""
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert len(file.function_calls) == 2

        # Check if the function calls are awaited
        assert file.function_calls[0].is_awaited
        assert not file.function_calls[1].is_awaited


def test_awaited_function_call_is_awaited(tmpdir) -> None:
    # language=typescript
    file = """
export const processData = async (input: string): Promise<string> =>
  await mainOperation(() => formatData`process ${input} value`)
"""

    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert len(file.function_calls) == 2

        # Check if the function calls are awaited
        assert file.function_calls[0].is_awaited
        assert file.function_calls[1].is_awaited


def test_function_call_is_awaited_nested_return(tmpdir) -> None:
    # language=typescript
    file = """
    await outer(() => {
        const x = inner();  // not awaited
        return finalInner();  // awaited since it's returned to awaited call
    });
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert len(file.function_calls) == 3
        assert file.function_calls[0].is_awaited  # outer
        assert not file.function_calls[1].is_awaited  # inner
        assert file.function_calls[2].is_awaited  # finalInner


def test_function_call_is_awaited_async_callbacks(tmpdir) -> None:
    # language=typescript
    file = """
    await first(async () => {
        second();  // not awaited despite being in async function
        await third();  // awaited explicitly
        return await fourth();  // awaited explicitly
    });
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert len(file.function_calls) == 4
        assert file.function_calls[0].is_awaited  # first
        assert not file.function_calls[1].is_awaited  # second
        assert file.function_calls[2].is_awaited  # third
        assert file.function_calls[3].is_awaited  # fourth


def test_function_call_is_awaited_conditional_returns(tmpdir) -> None:
    # language=typescript
    file = """
    await outsideFunc(value => {
        if (value) {
            insideIf();  // not awaited
            return earlyReturn();  // awaited (explicit return)
        }
        middleFunc();  // not awaited
        return value ?
            ternaryTrue() :  // awaited (implicit return)
            ternaryFalse();  // awaited (implicit return)
    });
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"test.ts": file}) as ctx:
        file = ctx.get_file("test.ts")
        assert len(file.function_calls) == 6
        assert file.function_calls[0].is_awaited  # outsideFunc
        assert not file.function_calls[1].is_awaited  # insideIf
        assert file.function_calls[2].is_awaited  # earlyReturn
        assert not file.function_calls[3].is_awaited  # middleFunc
        assert file.function_calls[4].is_awaited  # ternaryTrue
        assert file.function_calls[5].is_awaited  # ternaryFalse
