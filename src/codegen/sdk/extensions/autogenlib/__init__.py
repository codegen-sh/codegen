"""Automatic code generation library using OpenAI."""

import sys
from ._finder import AutoLibFinder
from ._exception_handler import setup_exception_handler


_sentinel = object()


def init(desc=_sentinel, enable_exception_handler=None, enable_caching=None):
    """Initialize autogenlib with a description of the functionality needed.

    Args:
        desc (str): A description of the library you want to generate.
        enable_exception_handler (bool): Whether to enable the global exception handler
            that sends exceptions to LLM for fix suggestions. Default is True.
        enable_caching (bool): Whether to enable caching of generated code. Default is False.
    """
    # Update the global description
    from . import _state

    if desc is not _sentinel:
        _state.description = desc
    if enable_exception_handler is not None:
        _state.exception_handler_enabled = enable_exception_handler
    if enable_caching is not None:
        _state.caching_enabled = enable_caching

    # Set up exception handler if enabled
    if _state.exception_handler_enabled:
        from ._exception_handler import setup_exception_handler

        setup_exception_handler()

    # Add our custom finder to sys.meta_path if it's not already there
    for finder in sys.meta_path:
        if isinstance(finder, AutoLibFinder):
            return
    sys.meta_path.insert(0, AutoLibFinder())


def set_exception_handler(enabled=True):
    """Enable or disable the exception handler.

    Args:
        enabled (bool): Whether to enable the exception handler. Default is True.
    """
    from . import _state

    _state.exception_handler_enabled = enabled


def set_caching(enabled=True):
    """Enable or disable caching.

    Args:
        enabled (bool): Whether to enable caching. Default is True.
    """
    from . import _state

    _state.caching_enabled = enabled


__all__ = ["init", "set_exception_handler", "setup_exception_handler", "set_caching"]

init()
