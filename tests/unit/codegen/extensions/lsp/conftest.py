import sys

import pytest_lsp
from lsprotocol.types import (
    InitializeParams,
)
from pytest_lsp import (
    ClientServerConfig,
    LanguageClient,
    client_capabilities,
)

from codegen.sdk.core.codebase import Codebase


@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "codegen.extensions.lsp.lsp"],
    ),
)
async def lsp_client_uninitialized(lsp_client: LanguageClient):
    yield lsp_client
    await lsp_client.shutdown_session()


@pytest_lsp.fixture(
    config=ClientServerConfig(
        server_command=[sys.executable, "-m", "codegen.extensions.lsp.lsp"],
    ),
)
async def client(lsp_client: LanguageClient, codebase: Codebase):
    # Setup
    response = await lsp_client.initialize_session(
        InitializeParams(
            capabilities=client_capabilities("visual-studio-code"),
            root_uri="file://" + str(codebase.repo_path.resolve()),
            root_path=str(codebase.repo_path.resolve()),
        )
    )

    yield

    # Teardown
    await lsp_client.shutdown_session()
