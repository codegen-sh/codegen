#!/usr/bin/env bash
TESTS_TO_RUN=$(uv run --frozen pytest --collect-only ${PYTEST_ARGS} -q --disable-warnings --no-summary --no-header)
TESTS_TO_RUN=$(echo "${TESTS_TO_RUN}" | head -n -2)
echo $TESTS_TO_RUN
