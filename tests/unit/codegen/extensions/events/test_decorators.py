"""Tests for CodegenApp decorators."""

import unittest
from unittest.mock import MagicMock, patch

from codegen.extensions.events import CodegenApp
from codegen.extensions.events.decorators import snapshot_codebase, with_codebase


class TestCodegenAppDecorators(unittest.TestCase):
    """Test cases for CodegenApp decorators."""

    @patch("codegen.extensions.events.decorators.Codebase")
    def test_with_codebase_decorator(self, mock_codebase_class):
        """Test the with_codebase decorator."""
        # Create a mock codebase
        mock_codebase = MagicMock()
        mock_codebase._op.repo_config.organization_name = "test-org"
        mock_codebase._op.repo_name = "test-repo"

        # Apply the decorator
        @with_codebase(mock_codebase)
        class TestApp(CodegenApp):
            pass

        # Initialize the app
        app = TestApp(name="test-app")

        # Check that the codebase was added to the app
        self.assertIn("test-org/test-repo", app.codebases)
        self.assertEqual(app.codebases["test-org/test-repo"], mock_codebase)

    @patch("codegen.extensions.events.decorators.Codebase")
    def test_snapshot_codebase_decorator(self, mock_codebase_class):
        """Test the snapshot_codebase decorator."""
        # Set up the mock
        mock_codebase = MagicMock()
        mock_codebase_class.from_repo.return_value = mock_codebase

        # Apply the decorator
        @snapshot_codebase("test-org/test-repo")
        class TestApp(CodegenApp):
            pass

        # Initialize the app
        app = TestApp(name="test-app")

        # Check that Codebase.from_repo was called with the correct arguments
        mock_codebase_class.from_repo.assert_called_once_with("test-org/test-repo", tmp_dir="/tmp/codegen")

        # Check that the codebase was added to the app
        self.assertIn("test-org/test-repo", app.codebases)
        self.assertEqual(app.codebases["test-org/test-repo"], mock_codebase)

    @patch("codegen.extensions.events.decorators.Codebase")
    def test_snapshot_codebase_decorator_with_custom_tmp_dir(self, mock_codebase_class):
        """Test the snapshot_codebase decorator with a custom tmp_dir."""
        # Set up the mock
        mock_codebase = MagicMock()
        mock_codebase_class.from_repo.return_value = mock_codebase

        # Apply the decorator with a custom tmp_dir
        @snapshot_codebase("test-org/test-repo", tmp_dir="/custom/tmp/dir")
        class TestApp(CodegenApp):
            pass

        # Initialize the app
        app = TestApp(name="test-app")

        # Check that Codebase.from_repo was called with the correct arguments
        mock_codebase_class.from_repo.assert_called_once_with("test-org/test-repo", tmp_dir="/custom/tmp/dir")

        # Check that the codebase was added to the app
        self.assertIn("test-org/test-repo", app.codebases)
        self.assertEqual(app.codebases["test-org/test-repo"], mock_codebase)

    @patch("codegen.extensions.events.decorators.Codebase")
    def test_snapshot_codebase_decorator_exception(self, mock_codebase_class):
        """Test the snapshot_codebase decorator when an exception occurs."""
        # Set up the mock to raise an exception
        mock_codebase_class.from_repo.side_effect = Exception("Test exception")

        # Apply the decorator
        @snapshot_codebase("test-org/test-repo")
        class TestApp(CodegenApp):
            pass

        # Initialize the app should raise an exception
        with self.assertRaises(Exception) as context:
            TestApp(name="test-app")

        # Check that the exception message is correct
        self.assertEqual(str(context.exception), "Test exception")


if __name__ == "__main__":
    unittest.main()
