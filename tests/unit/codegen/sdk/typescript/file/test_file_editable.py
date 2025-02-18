from codegen.sdk.codebase.factory.get_session import get_codebase_session
from codegen.shared.enums.programming_language import ProgrammingLanguage


def test_add_symbol_arrow_function(tmpdir) -> None:
    # language=typescript jsx
    content = """
const Component: React.FC = () => {
  return <div>Component Content</div>;
};
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"file.tsx": content}) as codebase:
        file = codebase.get_file("file.tsx")
        new_file = codebase.create_file("new_file.tsx", "")
        new_file.add_symbol(file.get_function("Component"))

    # language=typescript jsx
    assert (
        new_file.content
        == """

export const Component: React.FC = () => {
  return <div>Component Content</div>;
};"""
    )


def test_file_search_exclude_comments(tmpdir) -> None:
    """Make sure that we can exclude comments from the search results."""
    # language=typescript
    content = """

const test = () => {
    const MATCH_LITERAL = 123;
    // COMMENT_TEXT
    /*
        MULTILINE_COMMENT_TEXT
    */
    const stringVar = "STRING_TEXT";
    const templateStringVar = `TEMPLATE_STRING_TEXT`;
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"file.ts": content}) as codebase:
        file = codebase.get_file("file.ts")
        regex_pattern = r"\b[A-Z_]+\b"

        # =====[ Test with neither ]=====
        matches = file.search(regex_pattern, include_strings=False, include_comments=False)
        assert len(matches) == 1

        # =====[ Test with include_comments=True ]=====
        matches = file.search(regex_pattern, include_strings=False, include_comments=True)
        assert len(matches) == 3

        # =====[ Test with include_strings=True ]=====
        matches = file.search(regex_pattern, include_strings=True, include_comments=False)
        assert len(matches) == 3

        # =====[ Test with both include_strings=True and include_comments=True ]=====
        matches = file.search(regex_pattern, include_strings=True, include_comments=True)
        assert len(matches) == 5


def test_file_search_exclude_comments_2(tmpdir) -> None:
    """Make sure that we can exclude comments from the search results."""
    # language=typescript
    content = """
function processData({
    result: {
        terms,
        block: { text },
    },
    processor: { queryLower },
}: ProcessingArgs) {
    // NOTE: Replace implementation
    const calculator = {
        compute(x: any, y: any, z: any) {
            return 0
        },
    }
    const blockLower = text.toLowerCase()
    return {
        name: "CALCULATION_RESULT",
        value: normalizeValue(
            calculator.compute(queryLower, blockLower, {
                useCollator: true,
            }) / blockLower.length,
        ),
    } as const satisfies NumericEntry
}
    """
    with get_codebase_session(tmpdir=tmpdir, programming_language=ProgrammingLanguage.TYPESCRIPT, files={"file.ts": content}) as codebase:
        file = codebase.get_file("file.ts")
        regex_pattern = r"!!\s*(\w+|\([^\)]*\))"

        # =====[ Test with neither ]=====
        matches = file.search(regex_pattern, include_strings=False, include_comments=False)
        assert len(matches) == 0
