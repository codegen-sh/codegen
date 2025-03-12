from typing import Callable

import pytest
from lsprotocol.types import (
    DidChangeTextDocumentParams,
    DidCloseTextDocumentParams,
    DidOpenTextDocumentParams,
    Position,
    Range,
    RenameParams,
    TextDocumentContentChangeEvent,
    TextDocumentContentChangePartial,
    TextDocumentContentParams,
    TextDocumentIdentifier,
    TextDocumentItem,
    VersionedTextDocumentIdentifier,
)
from pytest_lsp import LanguageClient

from codegen.sdk.core.codebase import Codebase
from tests.unit.codegen.extensions.lsp.utils import apply_edit


@pytest.fixture()
def document_uri(codebase: Codebase, request) -> str:
    return request.param.format(workspaceFolder=str(codebase.repo_path))


@pytest.mark.parametrize(
    "original, document_uri",
    [
        (
            {
                "test.py": """
def example_function():
    pass
                """.strip(),
            },
            "file://{workspaceFolder}/test.py",
        ),
    ],
    indirect=True,
)
async def test_did_open(
    client: LanguageClient,
    codebase: Codebase,
    original: dict,
    document_uri: str,
):
    # Send didOpen notification
    client.text_document_did_open(
        params=DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=document_uri,
                language_id="python",
                version=1,
                text=original["test.py"],
            )
        )
    )

    # Verify the file is in the workspace
    document = await client.workspace_text_document_content_async(TextDocumentContentParams(uri=document_uri))
    assert document is not None
    assert document.text == original["test.py"]


@pytest.mark.parametrize(
    "original, document_uri, changes, expected_text",
    [
        (
            {
                "test.py": """
def example_function():
    pass
                """.strip(),
            },
            "file://{workspaceFolder}/test.py",
            [
                TextDocumentContentChangePartial(
                    range=Range(
                        start=Position(line=1, character=4),
                        end=Position(line=1, character=8),
                    ),
                    text="return True",
                ),
            ],
            """
def example_function():
    return True
            """.strip(),
        ),
    ],
    ids=["example_function"],
    indirect=["document_uri", "original"],
)
async def test_did_change(
    client: LanguageClient,
    codebase: Codebase,
    original: dict,
    document_uri: str,
    changes: list[TextDocumentContentChangeEvent],
    expected_text: str,
):
    # First open the document
    client.text_document_did_open(
        params=DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=document_uri,
                language_id="python",
                version=1,
                text=original["test.py"],
            )
        )
    )

    # Send didChange notification
    client.text_document_did_change(
        params=DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(
                uri=document_uri,
                version=2,
            ),
            content_changes=changes,
        )
    )

    # Verify the changes were applied
    document = await client.workspace_text_document_content_async(TextDocumentContentParams(uri=document_uri))
    assert document is not None
    assert document.text == expected_text


@pytest.mark.parametrize(
    "original, document_uri",
    [
        (
            {
                "test.py": """
def example_function():
    pass
                """.strip(),
            },
            "file://{worskpaceFolder}/test.py",
        ),
    ],
)
async def test_did_close(
    client: LanguageClient,
    codebase: Codebase,
    original: dict,
    document_uri: str,
):
    document_uri = document_uri.format(worskpaceFolder=str(codebase.repo_path))
    # First open the document
    client.text_document_did_open(
        params=DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=document_uri,
                language_id="python",
                version=1,
                text=original["test.py"],
            )
        )
    )

    # Send didClose notification
    client.text_document_did_close(params=DidCloseTextDocumentParams(text_document=TextDocumentIdentifier(uri=document_uri)))

    # Verify the document is removed from the workspace
    document = await client.workspace_text_document_content_async(TextDocumentContentParams(uri=document_uri))
    assert document.text == original["test.py"]


@pytest.mark.parametrize(
    "original, document_uri, position, new_name, expected",
    [
        (
            {
                "test.py": """
def example_function():
    pass

def main():
    example_function()
                """.strip(),
            },
            "file://{workspaceFolder}/test.py",
            Position(line=0, character=5),  # Position of 'example_function'
            "renamed_function",
            {
                "test.py": """
def renamed_function():
    pass # modified

def main():
    renamed_function()
                """.strip(),
            },
        ),
    ],
    indirect=["document_uri", "original"],
)
async def test_rename_after_sync(
    client: LanguageClient,
    codebase: Codebase,
    original: dict,
    document_uri: str,
    position: Position,
    new_name: str,
    assert_expected: Callable,
):
    # First open the document
    client.text_document_did_open(
        params=DidOpenTextDocumentParams(
            text_document=TextDocumentItem(
                uri=document_uri,
                language_id="python",
                version=1,
                text=original["test.py"],
            )
        )
    )

    # Make a change to the document
    client.text_document_did_change(
        params=DidChangeTextDocumentParams(
            text_document=VersionedTextDocumentIdentifier(
                uri=document_uri,
                version=2,
            ),
            content_changes=[
                TextDocumentContentChangePartial(
                    range=Range(
                        start=Position(line=1, character=4),
                        end=Position(line=1, character=8),
                    ),
                    text="pass # modified",
                ),
            ],
        )
    )

    # Perform rename operation
    result = await client.text_document_rename_async(
        params=RenameParams(
            text_document=TextDocumentIdentifier(uri=document_uri),
            position=position,
            new_name=new_name,
        )
    )
    if result:
        apply_edit(codebase, result)
    assert_expected(codebase)
