import pytest
from lsprotocol.types import (
    DefinitionParams,
    Location,
    Position,
    Range,
    TextDocumentIdentifier,
)
from pytest_lsp import LanguageClient

from codegen.sdk.core.codebase import Codebase


@pytest.mark.parametrize(
    "original, position, expected_location",
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
            Position(line=4, character=4),  # Position of example_function call
            Location(
                uri="file://{workspaceFolder}/test.py",
                range=Range(
                    start=Position(line=0, character=4),
                    end=Position(line=0, character=20),
                ),
            ),
        ),
        (
            {
                "test.py": """
class MyClass:
    def method(self):
        pass

obj = MyClass()
obj.method()
                """.strip(),
            },
            Position(line=5, character=4),  # Position of method call
            Location(
                uri="file://{workspaceFolder}/test.py",
                range=Range(
                    start=Position(line=1, character=8),
                    end=Position(line=1, character=14),
                ),
            ),
        ),
        (
            {
                "module/utils.py": """
def utility_function():
    pass
                """.strip(),
                "test.py": """
from module.utils import utility_function

def main():
    utility_function()
                """.strip(),
            },
            Position(line=3, character=4),  # Position of utility_function call in test.py
            Location(
                uri="file://{workspaceFolder}/module/utils.py",
                range=Range(
                    start=Position(line=0, character=4),
                    end=Position(line=0, character=20),  # Adjusted to end before ()
                ),
            ),
        ),
        (
            {
                "models.py": """
class DatabaseModel:
    def save(self):
        pass
                """.strip(),
                "test.py": """
from models import DatabaseModel

def main():
    model = DatabaseModel()
    model.save()
                """.strip(),
            },
            Position(line=4, character=10),  # Position of save() call in test.py
            Location(
                uri="file://{workspaceFolder}/models.py",
                range=Range(
                    start=Position(line=1, character=8),
                    end=Position(line=1, character=12),  # Adjusted to end before ()
                ),
            ),
        ),
        (
            {
                "module/__init__.py": """
from .constants import DEFAULT_TIMEOUT
                """.strip(),
                "module/constants.py": """
DEFAULT_TIMEOUT = 30
                """.strip(),
                "test.py": """
from module import DEFAULT_TIMEOUT

def main():
    timeout = DEFAULT_TIMEOUT
                """.strip(),
            },
            Position(line=3, character=14),  # Position of DEFAULT_TIMEOUT reference in test.py
            Location(
                uri="file://{workspaceFolder}/module/constants.py",
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=0, character=15),  # Adjusted to end before =
                ),
            ),
        ),
    ],
)
async def test_go_to_definition(
    client: LanguageClient,
    codebase: Codebase,
    original: dict,
    position: Position,
    expected_location: Location,
):
    result = await client.text_document_definition_async(
        params=DefinitionParams(
            text_document=TextDocumentIdentifier(uri=f"file://{codebase.repo_path}/test.py"),
            position=position,
        )
    )

    assert isinstance(result, Location)
    assert result.uri == expected_location.uri.format(workspaceFolder=str(codebase.repo_path))
    assert result.range == expected_location.range
