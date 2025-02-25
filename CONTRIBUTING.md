# Contributing to Codegen

Thank you for your interest in contributing to Codegen! This document outlines the process and guidelines for contributing. If you have any questions, please join our [Slack Community](https://community.codegen.com) 😀.

## Contributor License Agreement

By contributing to Codegen, you agree that:

1. Your contributions will be licensed under the project's license.
1. You have the right to license your contribution under the project's license.
1. You grant Codegen a perpetual, worldwide, non-exclusive, royalty-free license to use your contribution.

See our [CLA](CLA.md) for more details.

# Development Setup

This guide will help you set up the development environment for this project.

## Installing UV Package Manager

UV is a fast Python package installer and resolver.

### macOS

Install UV using Homebrew:

```bash
brew install uv
```

### Debian/Ubuntu

#### Install Required Dependencies

Before installing UV, ensure `clang` and `curl` are installed:

```bash
sudo apt-get update
sudo apt-get install -y clang curl
```

> **Note**: `clang` is required for compilation steps during `uv sync`.

#### Install UV

Once dependencies are installed, install UV:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

For other platforms, refer to the [UV installation docs](https://github.com/astral-sh/uv).

## Setting Up the Development Environment

After installing UV, set up your development environment:

```bash
uv venv
source .venv/bin/activate
uv sync --dev
```

### Troubleshooting

- If `uv sync` fails with `missing field 'version'`, it may be due to an older version of uv incompatible with the lock file. Try:

  ```bash
  uv self update
  uv sync --dev
  ```

- If `uv sync` fails due to a compilation error, ensure `clang` is installed and then rerun:

  ```bash
  uv sync --dev
  ```

### Running Tests

```bash
# Unit tests (tests atomic functionality)
uv run pytest tests/unit -n auto

# Codemod tests (tests larger programs)
uv run pytest tests/integration/codemod/test_codemods.py -n auto
```

## Pull Request Process

1. Fork the repository and create your branch from `develop`.
1. Ensure your code passes all tests.
1. Update documentation as needed.
1. Submit a pull request to the `develop` branch.
1. Include a clear description of your changes in the PR.

## Release Process

First you must wait for all required checks to pass before releasing.
Create a git tag and push it to develop to trigger a new release:

```bash
git switch develop
git pull
git tag v0.YOUR_VERSION
git push origin v0.YOUR_VERSION
```

This will trigger a release job to build this new version.
