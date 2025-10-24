import unittest
from pathlib import Path

from codegen.git.schemas.repo_config import RepoConfig


class TestRepoConfig(unittest.TestCase):
    def test_repo_path_with_organization(self):
        """Test that repo_path includes organization name when available."""
        config = RepoConfig(name="test-repo", full_name="test-org/test-repo", base_dir="/tmp")
        self.assertEqual(config.repo_path, Path("/tmp/test-org/test-repo"))

    def test_repo_path_without_organization(self):
        """Test that repo_path falls back to base_dir/name when organization is not available."""
        config = RepoConfig(name="test-repo", base_dir="/tmp")
        self.assertEqual(config.repo_path, Path("/tmp/test-repo"))

    def test_organization_name_extraction(self):
        """Test that organization_name is correctly extracted from full_name."""
        config = RepoConfig(name="test-repo", full_name="test-org/test-repo")
        self.assertEqual(config.organization_name, "test-org")

    def test_organization_name_none(self):
        """Test that organization_name is None when full_name is not provided."""
        config = RepoConfig(name="test-repo")
        self.assertIsNone(config.organization_name)


if __name__ == "__main__":
    unittest.main()
