import uuid

import pytest
from lsprotocol import types
from pytest_lsp import LanguageClient, client_capabilities

from codegen.sdk.core.codebase import Codebase
from tests.unit.codegen.extensions.lsp.utils import apply_edit


def check_ascending(reports: list[types.WorkDoneProgressReport]):
    prev = 0
    for report in reports:
        if isinstance(report, types.WorkDoneProgressEnd) or report.percentage is None:
            continue
        assert report.percentage > prev
        prev = report.percentage


def check_reports(reports: list[types.WorkDoneProgressReport]):
    assert isinstance(reports[0], types.WorkDoneProgressBegin)
    assert isinstance(reports[-1], types.WorkDoneProgressEnd)
    check_ascending(reports)


@pytest.mark.parametrize(
    "original, expected",
    [
        (
            {
                "test.py": """
def hello():
    pass
""".strip(),
            },
            {
                "test.py": """
def world():
    pass
""".strip()
            },
        )
    ],
)
async def test_progress(lsp_client_uninitialized: LanguageClient, codebase: Codebase, assert_expected, original: dict[str, str]):
    token = str(uuid.uuid4())
    assert lsp_client_uninitialized.progress_reports.get(token, None) is None
    req = await lsp_client_uninitialized.initialize_session(
        types.InitializeParams(
            capabilities=client_capabilities("visual-studio-code"),
            root_uri="file://" + str(codebase.repo_path.resolve()),
            root_path=str(codebase.repo_path.resolve()),
            work_done_token=token,
        )
    )
    reports = lsp_client_uninitialized.progress_reports.get(token, None)
    assert reports is not None
    check_reports(reports)
    for file in original.keys():
        assert any(file in report.message for report in reports if isinstance(report, types.WorkDoneProgressReport))
    rename_token = str(uuid.uuid4())
    result = await lsp_client_uninitialized.text_document_rename_async(
        params=types.RenameParams(
            position=types.Position(line=0, character=5),
            text_document=types.TextDocumentIdentifier(uri=f"file://{codebase.repo_path}/test.py"),
            new_name="world",
            work_done_token=rename_token,
        )
    )
    if result:
        apply_edit(codebase, result)
    reports = lsp_client_uninitialized.progress_reports.get(rename_token, None)
    assert reports is not None
    check_reports(reports)
    assert "Renaming" in reports[0].title
    assert_expected(codebase)
