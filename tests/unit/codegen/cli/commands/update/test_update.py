import json
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner
from packaging.version import Version
from rich.text import Text

from codegen.cli.commands.update import main


@pytest.fixture(autouse=True)
def mock_request():
    """Patch requests.get to return a fake response loaded from our JSON file.
    Also records the URL(s) that were requested.
    """

    def fake_get(*_, **__):
        data = json.loads((Path(__file__).parent / "data" / "response.json").read_text())

        class FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return data

        return FakeResponse()

    with patch("requests.get", side_effect=fake_get) as mock:
        yield mock


@pytest.fixture(autouse=True)
def mock_install_package():
    with patch.object(main, "install_package") as mock_install:
        yield mock_install


@pytest.fixture(autouse=True)
def mock_distribution():
    with patch.object(main, "distribution") as mock_distribution:
        mock_distribution.return_value.version = "1.20.0"
        mock_distribution.return_value.name = "codegen"
        yield mock_distribution


def test_conflicting_options():
    """Test that passing both --list and --version raises a click exception."""
    runner = CliRunner()
    result = runner.invoke(main.update_command, ["--list", "--version", "0.3.0"])
    # The command should exit with non-zero exit code.
    assert result.exit_code != 0, "Expected a non-zero exit code when both --list and --version are provided."
    assert "Cannot specify both --list and --version" in Text.from_ansi(result.output).plain


def test_update_default(mock_install_package):
    """Test running the update command with no flags.
    According to the implementation, if no --list is provided then the branch
    'elif version:' is always taken (since version is redefined from distribution).
    """
    runner = CliRunner()
    result = runner.invoke(main.update_command, [])
    assert result.exit_code == 0

    mock_install_package.assert_called_once_with("codegen", "--upgrade")


def test_update_with_version_flag(mock_install_package):
    """Test running the update command with --version.
    Note: Due to the bug in update_command, the version provided on the command line
    is ignored and replaced by the version from distribution() (here always 1.0.0).
    """
    runner = CliRunner()
    result = runner.invoke(main.update_command, ["--version", "0.3.0"])
    assert result.exit_code == 0

    # Check that install_package was called with "codegen==0.3.0"
    mock_install_package.assert_called_once_with("codegen==0.3.0")


def test_list_versions(mock_request):
    """Test running the command with --list. This should:
    - Call requests.get with the expected URL.
    - Print a list of releases (only those that are considered new enough).
    - Mark the current version (1.0.0) with the [bold] formatting.
    """
    runner = CliRunner()
    result = runner.invoke(main.update_command, ["--list"])
    assert result.exit_code == 0

    mock_request.assert_called_once_with("https://pypi.org/pypi/codegen/json")

    output = result.output
    expected_lines = [
        "1.0",
        "1.19.0",
        "1.20.0 (current)",
        "1.21.0",
        "1.22.0",
        "1.22.1",
        "1.22.2",
        "1.23.0",
        "1.24.0",
        "1.24.1",
    ]
    for line in expected_lines:
        assert line in output, f"{line} should be in the output"


@pytest.mark.parametrize(
    "versions, current, num_prev, expected",
    [
        (["1.0.0", "1.0.1", "1.1.2", "1.2.3"], "1.0.0", 2, ["1.0.0", "1.0.1", "1.1.2", "1.2.3"]),
        (["0.4.5", "0.7.0", "1.0.0"], "1.0.0", 2, ["0.4.5", "0.7.0", "1.0.0"]),
        (["0.4.5", "0.7.0", "1.0.0"], "1.0.0", 1, ["0.7.0", "1.0.0"]),
        (["0.2.0", "0.3.0", "1.0.0"], "1.0.0", 0, ["1.0.0"]),
        (["0.2.0", "0.3.4", "0.3.5", "1.0.0"], "1.0.0", 1, ["0.3.4", "0.3.5", "1.0.0"]),
        (["0.5.1", "0.5.2", "0.6.0", "1.0.0"], "0.5.2", 1, ["0.5.1", "0.5.2", "0.6.0", "1.0.0"]),
    ],
    ids=["all_future_versions", "prev_2", "prev_1", "no_prev", "multiple_minor", "all_micros"],
)
def test_filter_versions(versions, current, num_prev, expected):
    """Test the filtering logic used to select releases to print."""
    filtered_versions = main.filter_versions([Version(v) for v in versions], Version(current), num_prev)
    assert filtered_versions == [Version(v) for v in expected]
