"""
Elixir-specific test configuration and fixtures.
"""

import os
import subprocess
import time
from pathlib import Path

import pytest


def ensure_elixir_test_repo_compiled(repo_path: str) -> None:
    """Ensure the Elixir test repository dependencies are installed and project is compiled.

    Next LS requires the project to be fully compiled and indexed before providing
    complete references and symbol resolution. This function:
    1. Installs dependencies via 'mix deps.get'
    2. Compiles the project via 'mix compile'

    This is essential in CI environments where dependencies aren't pre-installed.

    Args:
        repo_path: Path to the Elixir project root directory

    """
    # Check if this looks like an Elixir project
    mix_file = os.path.join(repo_path, "mix.exs")
    if not os.path.exists(mix_file):
        return

    # Check if already compiled (optimization for repeated runs)
    build_path = os.path.join(repo_path, "_build")
    deps_path = os.path.join(repo_path, "deps")

    if os.path.exists(build_path) and os.path.exists(deps_path):
        print(f"Elixir test repository already compiled in {repo_path}")
        return

    try:
        print("Installing dependencies and compiling Elixir test repository for optimal Next LS performance...")

        # First, install dependencies with increased timeout for CI
        print("=" * 60)
        print("Step 1/2: Installing Elixir dependencies...")
        print("=" * 60)
        start_time = time.time()

        deps_result = subprocess.run(
            ["mix", "deps.get"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,  # 3 minutes for dependency installation (CI can be slow)
        )

        deps_duration = time.time() - start_time
        print(f"Dependencies installation completed in {deps_duration:.2f} seconds")

        # Always log the output for transparency
        if deps_result.stdout.strip():
            print("Dependencies stdout:")
            print("-" * 40)
            print(deps_result.stdout)
            print("-" * 40)

        if deps_result.stderr.strip():
            print("Dependencies stderr:")
            print("-" * 40)
            print(deps_result.stderr)
            print("-" * 40)

        if deps_result.returncode != 0:
            print(f"⚠️  Warning: Dependencies installation failed with exit code {deps_result.returncode}")
            # Continue anyway - some projects might not have dependencies
        else:
            print("✓ Dependencies installed successfully")

        # Then compile the project with increased timeout for CI
        print("=" * 60)
        print("Step 2/2: Compiling Elixir project...")
        print("=" * 60)
        start_time = time.time()

        compile_result = subprocess.run(
            ["mix", "compile"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=300,
            check=False,  # 5 minutes for compilation (Credo compilation can be slow in CI)
        )

        compile_duration = time.time() - start_time
        print(f"Compilation completed in {compile_duration:.2f} seconds")

        # Always log the output for transparency
        if compile_result.stdout.strip():
            print("Compilation stdout:")
            print("-" * 40)
            print(compile_result.stdout)
            print("-" * 40)

        if compile_result.stderr.strip():
            print("Compilation stderr:")
            print("-" * 40)
            print(compile_result.stderr)
            print("-" * 40)

        if compile_result.returncode == 0:
            print(f"✓ Elixir test repository compiled successfully in {repo_path}")
        else:
            print(f"⚠️  Warning: Compilation completed with exit code {compile_result.returncode}")
            # Still continue - warnings are often non-fatal

        print("=" * 60)
        print(f"Total setup time: {time.time() - (start_time - compile_duration - deps_duration):.2f} seconds")
        print("=" * 60)

    except subprocess.TimeoutExpired as e:
        print("=" * 60)
        print(f"❌ TIMEOUT: Elixir setup timed out after {e.timeout} seconds")
        print(f"Command: {' '.join(e.cmd)}")
        print("This may indicate slow CI environment - Next LS may still work but with reduced functionality")

        # Try to get partial output if available
        if hasattr(e, "stdout") and e.stdout:
            print("Partial stdout before timeout:")
            print("-" * 40)
            print(e.stdout)
            print("-" * 40)
        if hasattr(e, "stderr") and e.stderr:
            print("Partial stderr before timeout:")
            print("-" * 40)
            print(e.stderr)
            print("-" * 40)
        print("=" * 60)

    except FileNotFoundError:
        print("❌ ERROR: 'mix' command not found - Elixir test repository may not be compiled")
        print("Please ensure Elixir is installed and available in PATH")
    except Exception as e:
        print(f"❌ ERROR: Failed to prepare Elixir test repository: {e}")


@pytest.fixture(scope="session", autouse=True)
def setup_elixir_test_environment():
    """Automatically prepare Elixir test environment for all Elixir tests.

    This fixture runs once per test session and automatically:
    1. Installs dependencies via 'mix deps.get'
    2. Compiles the Elixir test repository via 'mix compile'

    It uses autouse=True so it runs automatically without needing to be explicitly
    requested by tests. This ensures Next LS has a fully prepared project to work with.

    Uses generous timeouts (3-5 minutes) to accommodate slow CI environments.
    All output is logged for transparency and debugging.
    """
    # Get the test repo path relative to this conftest.py file
    test_repo_path = Path(__file__).parent.parent.parent / "resources" / "repos" / "elixir" / "test_repo"
    ensure_elixir_test_repo_compiled(str(test_repo_path))
    return str(test_repo_path)


@pytest.fixture(scope="session")
def elixir_test_repo_path(setup_elixir_test_environment):
    """Get the path to the prepared Elixir test repository.

    This fixture depends on setup_elixir_test_environment to ensure dependencies
    are installed and compilation has completed before returning the path.
    """
    return setup_elixir_test_environment
