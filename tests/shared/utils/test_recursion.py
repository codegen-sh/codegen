import sys
import pytest
from unittest.mock import patch, MagicMock

from tests.shared.utils.recursion import set_recursion_limit


def test_set_recursion_limit_windows():
    """Test that set_recursion_limit works on Windows without trying to import resource."""
    with patch('sys.platform', 'win32'), \
         patch('sys.setrecursionlimit') as mock_setrecursion, \
         patch('importlib.import_module') as mock_import:
        set_recursion_limit()
        mock_setrecursion.assert_called_once_with(10**9)
        mock_import.assert_not_called()


def test_set_recursion_limit_linux():
    """Test that set_recursion_limit works on Linux with resource module."""
    mock_resource = MagicMock()
    mock_resource.RLIM_INFINITY = -1
    mock_resource.RLIMIT_STACK = 8

    with patch('sys.platform', 'linux'), \
         patch('sys.setrecursionlimit') as mock_setrecursion, \
         patch('importlib.import_module', return_value=mock_resource) as mock_import:
        set_recursion_limit()
        mock_setrecursion.assert_called_once_with(10**9)
        mock_import.assert_called_once_with('resource')
        mock_resource.setrlimit.assert_called_once_with(8, (-1, -1)) 
