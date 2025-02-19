"""Utilities for working with language models and datasets."""

from dataclasses import dataclass
from typing import Optional

import requests


@dataclass
class SweBenchExample:
    """A single example from the SWE-bench dataset."""

    repo: str
    instance_id: str
    base_commit: str
    patch: str
    test_patch: str
    problem_statement: str
    hints_text: Optional[str]
    created_at: str
    version: str
    fail_to_pass: str
    pass_to_pass: Optional[str]
    environment_setup_commit: Optional[str]


def get_swe_bench_examples() -> list[SweBenchExample]:
    """Fetch examples from the SWE-bench dataset.

    Returns:
        List of SweBenchExample objects

    Raises:
        requests.RequestException: If the API request fails
    """
    url = "https://datasets-server.huggingface.co/rows"
    params = {
        "dataset": "princeton-nlp/SWE-bench",
        "config": "default",
        "split": "dev",
        "offset": 0,
        "length": 100,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    examples = []
    for row in data["rows"]:
        example = SweBenchExample(
            repo=row["row"]["repo"],
            instance_id=row["row"]["instance_id"],
            base_commit=row["row"]["base_commit"],
            patch=row["row"]["patch"],
            test_patch=row["row"]["test_patch"],
            problem_statement=row["row"]["problem_statement"],
            hints_text=row["row"].get("hints_text"),
            created_at=row["row"]["created_at"],
            version=row["row"]["version"],
            fail_to_pass=row["row"]["FAIL_TO_PASS"],
            pass_to_pass=row["row"].get("PASS_TO_PASS"),
            environment_setup_commit=row["row"].get("environment_setup_commit"),
        )
        examples.append(example)

    return examples
