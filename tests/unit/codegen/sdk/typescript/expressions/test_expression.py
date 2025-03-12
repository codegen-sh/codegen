from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_function_calls_from_function_call(tmpdir):
    # language=typescript
    content = """
describe("LoadManager test", () => {
    it("add an arbitary number of producers, numProducers should return correct count", () => {
      const numProducers = 8764
      addLoad(loadManager, numProducers, 0)
      expect(loadManager.numProducers()).toEqual(numProducers)
    })
})
    """
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        func_call = file.function_calls
        assert len(func_call) == 6


def test_remove_parenthesized(tmpdir):
    # language=typescript
    content = """
const a = (b) || c;
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.ts": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.ts")
        b = file.symbols[0].value.left
        b.remove()
    # language=typescript
    assert (
        file.content
        == """
const a = c;
"""
    )


def test_remove_tsx(tmpdir):
    # language=typescript jsx
    content = """
const element = <h1>Hello, {name}</h1>;
"""
    with get_codebase_session(tmpdir=tmpdir, files={"test.tsx": content}, programming_language=ProgrammingLanguage.TYPESCRIPT) as codebase:
        file = codebase.get_file("test.tsx", optional=False)
        elem = file.jsx_elements[0]
        name = elem.expressions[0].statement
        name.remove()
    # language=typescript jsx
    assert (
        file.content
        == """
const element = <h1>Hello, </h1>;
"""
    )
