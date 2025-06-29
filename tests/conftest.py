import os

import pytest


def find_dirs_to_ignore(start_dir, prefix):
    dirs_to_ignore = []
    for root, dirs, files in os.walk(start_dir):
        for dir in dirs:
            full_path = os.path.relpath(os.path.join(root, dir), start_dir)
            if any(dd.startswith("original_input") or dd.startswith("output") or dd.startswith("input") or dd.startswith("expected") for dd in dir.split("/")):
                dirs_to_ignore.append(full_path)
    return dirs_to_ignore


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--profile",
        action="store",
        type=bool,
        default=False,
        help="Whether to profile the test",
    )
    parser.addoption(
        "--sync-graph",
        action="store",
        type=str,
        dest="sync-graph",
        default="false",
        help="Whether to sync the graph between tests",
    )
    parser.addoption(
        "--log-parse",
        action="store",
        type=str,
        dest="log-parse",
        default="false",
        help="Whether to log parsing errors for parse tests",
    )
    parser.addoption(
        "--extra-repos",
        type=bool,
        action="store",
        default=False,
        help="Whether to test on extra repos",
    )
    parser.addoption("--token", action="store", default=None, help="Read-only GHA token to access extra repos")

    parser.addoption("--codemod-id", action="store", type=int, default=None, help="Runs db skills test for a specific codemod")

    parser.addoption("--repo-id", action="store", type=int, default=None, help="Runs db skills test for a specific repo")

    parser.addoption("--base-commit", action="store", type=str, default=None, help="Runs db skills test for a specific commit. Argument can be the shortest unique substring.")

    parser.addoption("--cli-api-key", action="store", type=str, default=None, help="Token necessary to access skills.")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        if "NodeJS or npm is not installed" in str(report.longrepr):
            msg = "This test requires NodeJS and npm to be installed. Please install them before running the tests."
            raise RuntimeError(msg)
