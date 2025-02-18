from collections.abc import Sequence
from typing import cast

import pytest
from lsprotocol.types import (
    DocumentSymbol,
    DocumentSymbolParams,
    Position,
    Range,
    SymbolKind,
    TextDocumentIdentifier,
)
from pytest_lsp import LanguageClient

from codegen.sdk.core.codebase import Codebase


@pytest.mark.parametrize(
    "original, expected_symbols",
    [
        (
            {
                "test.py": """
class TestClass:
    def test_method(self):
        pass

def top_level_function():
    pass
                """.strip(),
            },
            [
                DocumentSymbol(
                    name="TestClass",
                    kind=SymbolKind.Class,
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=2, character=12),
                    ),
                    selection_range=Range(
                        start=Position(line=0, character=6),
                        end=Position(line=0, character=15),
                    ),
                    children=[
                        DocumentSymbol(
                            name="test_method",
                            kind=SymbolKind.Method,
                            range=Range(
                                start=Position(line=1, character=4),
                                end=Position(line=2, character=12),
                            ),
                            selection_range=Range(
                                start=Position(line=1, character=8),
                                end=Position(line=1, character=19),
                            ),
                            children=[],
                        )
                    ],
                ),
                DocumentSymbol(
                    name="top_level_function",
                    kind=SymbolKind.Function,
                    range=Range(
                        start=Position(line=4, character=0),
                        end=Position(line=5, character=8),
                    ),
                    selection_range=Range(
                        start=Position(line=4, character=4),
                        end=Position(line=4, character=22),
                    ),
                    children=[],
                ),
            ],
        ),
        (
            {
                "test.py": """
@decorator
class OuterClass:
    class InnerClass:
        @property
        def inner_method(self):
            pass

    async def outer_method(self):
        pass

@decorator
async def async_function():
    pass
                """.strip(),
            },
            [
                DocumentSymbol(
                    name="OuterClass",
                    kind=SymbolKind.Class,
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=8, character=12),
                    ),
                    selection_range=Range(
                        start=Position(line=1, character=6),
                        end=Position(line=1, character=16),
                    ),
                    children=[
                        DocumentSymbol(
                            name="InnerClass",
                            kind=SymbolKind.Class,
                            range=Range(
                                start=Position(line=2, character=4),
                                end=Position(line=5, character=16),
                            ),
                            selection_range=Range(
                                start=Position(line=2, character=10),
                                end=Position(line=2, character=20),
                            ),
                            children=[
                                DocumentSymbol(
                                    name="inner_method",
                                    kind=SymbolKind.Method,
                                    range=Range(
                                        start=Position(line=3, character=8),
                                        end=Position(line=5, character=16),
                                    ),
                                    selection_range=Range(
                                        start=Position(line=4, character=12),
                                        end=Position(line=4, character=24),
                                    ),
                                    children=[],
                                )
                            ],
                        ),
                        DocumentSymbol(
                            name="outer_method",
                            kind=SymbolKind.Method,
                            range=Range(
                                start=Position(line=7, character=4),
                                end=Position(line=8, character=12),
                            ),
                            selection_range=Range(
                                start=Position(line=7, character=14),
                                end=Position(line=7, character=26),
                            ),
                            children=[],
                        ),
                    ],
                ),
                DocumentSymbol(
                    name="async_function",
                    kind=SymbolKind.Function,
                    range=Range(
                        start=Position(line=10, character=0),
                        end=Position(line=12, character=8),
                    ),
                    selection_range=Range(
                        start=Position(line=11, character=10),
                        end=Position(line=11, character=24),
                    ),
                    children=[],
                ),
            ],
        ),
        (
            {
                "test.py": """
def function_with_args(arg1: str, arg2: int = 42):
    pass

class ClassWithDocstring:
    \"\"\"This is a docstring.\"\"\"
    def method_with_docstring(self):
        \"\"\"Method docstring.\"\"\"
        pass
                """.strip(),
            },
            [
                DocumentSymbol(
                    name="function_with_args",
                    kind=SymbolKind.Function,
                    range=Range(
                        start=Position(line=0, character=0),
                        end=Position(line=1, character=8),
                    ),
                    selection_range=Range(
                        start=Position(line=0, character=4),
                        end=Position(line=0, character=22),
                    ),
                    children=[],
                ),
                DocumentSymbol(
                    name="ClassWithDocstring",
                    kind=SymbolKind.Class,
                    range=Range(
                        start=Position(line=3, character=0),
                        end=Position(line=7, character=12),
                    ),
                    selection_range=Range(
                        start=Position(line=3, character=6),
                        end=Position(line=3, character=24),
                    ),
                    children=[
                        DocumentSymbol(
                            name="method_with_docstring",
                            kind=SymbolKind.Method,
                            range=Range(
                                start=Position(line=5, character=4),
                                end=Position(line=7, character=12),
                            ),
                            selection_range=Range(
                                start=Position(line=5, character=8),
                                end=Position(line=5, character=29),
                            ),
                            children=[],
                        ),
                    ],
                ),
            ],
        ),
    ],
)
async def test_document_symbols(
    client: LanguageClient,
    codebase: Codebase,
    original: dict,
    expected_symbols: list[DocumentSymbol],
):
    result = await client.text_document_document_symbol_async(params=DocumentSymbolParams(text_document=TextDocumentIdentifier(uri=f"file://{codebase.repo_path}/test.py")))

    assert result is not None
    symbols = cast(Sequence[DocumentSymbol], result)
    assert len(symbols) == len(expected_symbols)
    for actual, expected in zip(symbols, expected_symbols):
        assert actual.name == expected.name
        assert actual.kind == expected.kind
        assert actual.range == expected.range
        assert actual.selection_range == expected.selection_range
        assert actual.children == expected.children
        assert actual == expected
    assert symbols == expected_symbols
