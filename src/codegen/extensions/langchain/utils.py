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


def get_swe_bench_example(instance_id: str) -> SweBenchExample:
    """Fetch a single example from the SWE-bench dataset by its instance ID.

    Args:
        instance_id: The unique identifier of the example to fetch

    Returns:
        SweBenchExample object

    Raises:
        ValueError: If no example found with the given ID
        requests.RequestException: If the API request fails
    """
    url = "https://datasets-server.huggingface.co/filter"
    params = {
        "dataset": "princeton-nlp/SWE-bench",
        "config": "default",
        "split": "dev",
        "where": f"instance_id='{instance_id}'",
        "offset": 0,
        "length": 1,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if not data["rows"]:
        msg = f"No example found with instance_id: {instance_id}"
        raise ValueError(msg)

    row = data["rows"][0]["row"]
    return SweBenchExample(
        repo=row["repo"],
        instance_id=row["instance_id"],
        base_commit=row["base_commit"],
        patch=row["patch"],
        test_patch=row["test_patch"],
        problem_statement=row["problem_statement"],
        hints_text=row.get("hints_text"),
        created_at=row["created_at"],
        version=row["version"],
        fail_to_pass=row["FAIL_TO_PASS"],
        pass_to_pass=row.get("PASS_TO_PASS"),
        environment_setup_commit=row.get("environment_setup_commit"),
    )
