#!/usr/bin/env bash
uv tool install pre-commit --with pre-commit-uv
uv tool install deptry
uv tool update-shell
uv venv && source .venv/bin/activate
uv sync
pre-commit install
pre-commit install-hooks
