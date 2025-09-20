import logging

import click

from codegen.sdk.shared.logging.get_logger import get_logger

logger = get_logger(__name__)


@click.command(name="lsp")
def lsp_command():
    try:
        from codegen.sdk.extensions.lsp.lsp import server
    except (ImportError, ModuleNotFoundError):
        logger.exception("LSP is not installed. Please install it with `uv tool install graph-sitter[lsp] --prerelease=allow`")
        return
    logging.basicConfig(level=logging.INFO)
    server.start_io()
