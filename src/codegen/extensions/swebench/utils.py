import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from pprint import pprint
from typing import Literal, Optional

from datasets import load_dataset


class SWEBenchDataset(Enum):
    LITE = "princeton-nlp/SWE-bench_Lite"
    FULL = "princeton-nlp/SWE-bench"
    VERIFIED = "princeton-nlp/SWE-bench-verified"


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


def load_predictions(paths):
    prediction_paths = []
    for path in paths:
        path = Path(path)
        if path.is_file():
            prediction_paths.append(path)
        elif path.is_dir():
            prediction_paths += list(path.glob("*.json"))
        else:
            assert False, path

    # prediction_paths.sort(key=lambda p: p.stat().st_mtime)

    predictions = dict()
    for fname in prediction_paths:
        try:
            pred = json.loads(fname.read_text())
        except json.decoder.JSONDecodeError as err:
            pprint(fname)
            raise err

        if "instance_id" not in pred:
            print("Skipping json without instance_id", fname)
            continue

        inst = pred["instance_id"]
        pred["json_fname"] = str(fname)
        predictions[inst] = pred

    return predictions


def get_swe_bench_examples(
    dataset: SWEBenchDataset = SWEBenchDataset.LITE,
    split: Literal["train", "dev", "test"] = "test",
    offset: int = 0,
    length: int = 100,
    instance_id: str | None = None,
    repo: str | None = None,
) -> list[SweBenchExample]:
    """Fetch examples from the SWE-bench dataset using the datasets library.

    Args:
        dataset: The dataset to use ("lite", "full", or "verified")
        split: The dataset split to use
        offset: Starting index for examples
        length: Number of examples to fetch
        instance_id: Optional specific instance ID to fetch

    Returns:
        List of SweBenchExample objects
    """
    # Convert string dataset name to enum

    # Load the dataset with caching enabled
    swe_bench_dataset = load_dataset(dataset.value, download_mode="reuse_dataset_if_exists")

    # Get the requested split
    split_data = swe_bench_dataset[split]

    # Apply offset and length
    if instance_id or repo:
        offset = 0
        end_idx = len(split_data)
    else:
        end_idx = min(offset + length, len(split_data))
        if offset >= len(split_data):
            return []

    # Use the select method instead of slicing
    # This ensures we get dictionary-like objects
    selected_rows = split_data.select(range(offset, end_idx))

    # Convert to SweBenchExample objects
    examples = []
    for row in selected_rows:
        if instance_id and row["instance_id"] != instance_id:
            continue
        if repo and row["repo"] != repo:
            continue
        example = SweBenchExample(
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
        examples.append(example)

    return examples[:length]
