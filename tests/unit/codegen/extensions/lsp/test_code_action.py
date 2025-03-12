import logging
from collections import deque

import pytest
from lsprotocol import types
from lsprotocol.types import (
    CodeActionContext,
    CodeActionParams,
    Command,
    Position,
    Range,
    TextDocumentIdentifier,
)
from pytest_lsp import (
    LanguageClient,
)

from codegen.sdk.core.codebase import Codebase
from tests.unit.codegen.extensions.lsp.utils import apply_edit

logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "original, expected, actions",
    [
        #         (
        #             {
        #                 "test.py": """
        # def hello():
        #     pass
        # def world():
        #     hello()
        #          """.strip(),
        #             },
        #             {
        #                 "test.py": """
        # from hello import hello
        # def world():
        #     hello()
        #          """.strip(),
        #                 "hello.py": """
        # def hello():
        #     pass
        #          """.strip(),
        #             },
        #             [
        #                 CodeActionParams(
        #                     range=Range(
        #                         start=Position(line=0, character=0),
        #                         end=Position(line=2, character=4),
        #                     ),
        #                     text_document=TextDocumentIdentifier(uri="file://{workspaceFolder}/test.py"),
        #                     context=CodeActionContext(diagnostics=[]),
        #                 )
        #             ],
        #         ),
        (
            {
                "test.py": """
def test_a():
    pass

def test_b():
    pass
         """.strip(),
            },
            {
                "test_a.py": """

def test_a():
    pass""",
                "test_b.py": """

def test_b():
    pass""",
            },
            [
                CodeActionParams(
                    range=Range(
                        start=Position(line=0, character=4),
                        end=Position(line=0, character=11),
                    ),
                    text_document=TextDocumentIdentifier(uri="file://{workspaceFolder}/test.py"),
                    context=CodeActionContext(diagnostics=[]),
                )
            ],
        ),
    ],
    ids=[
        "split_tests",
    ],
)
async def test_code_action(
    client: LanguageClient,
    codebase: Codebase,
    assert_expected,
    actions: list[CodeActionParams],
):
    for action in actions:
        action.text_document.uri = action.text_document.uri.format(workspaceFolder=codebase.repo_path)

        result = await client.text_document_code_action_async(params=action)
        assert result is not None
        assert len(result) > 0
        to_execute = deque(result)
        while to_execute:
            edit = to_execute.popleft()
            if isinstance(edit, Command):
                assert not isinstance(edit.command, Command)
                await client.workspace_execute_command_async(types.ExecuteCommandParams(command=edit.command, arguments=edit.arguments))
            else:
                result = await client.code_action_resolve_async(edit)
                if result.edit:
                    apply_edit(codebase, result.edit)
                assert result is not None
                if result.command:
                    to_execute.append(result.command)

    assert_expected(codebase, check_codebase=False)
