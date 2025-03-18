import json
from dataclasses import dataclass
from pathlib import Path
from pprint import pprint
from typing import Literal, Optional

from datasets import load_dataset

from codegen.extensions.swebench.enums import SWEBenchDataset, SWEBenchLiteSubset
from codegen.extensions.swebench.subsets import LITE_SUBSETS
from codegen.extensions.swebench.success_rates import LITE_SUCCESS_RATES


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
    difficulty: Optional[int]


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


def get_difficulty(instance_id: str) -> int | None:
    if instance_id in LITE_SUCCESS_RATES:
        return 10 - int(LITE_SUCCESS_RATES[instance_id] * 10)
    return None


def get_swe_bench_examples(
    dataset: SWEBenchDataset | SWEBenchLiteSubset = SWEBenchLiteSubset.LITE_SMALL,
    split: Literal["train", "dev", "test"] = "test",
    length: int | None = None,
    instance_id: str | None = None,
    instance_ids: list[str] = [],
    repo: str | None = None,
) -> list[SweBenchExample]:
    """Fetch examples from the SWE-bench dataset using the datasets library.

    Args:
        dataset: The dataset to use ("lite", "full", or "verified")
        split: The dataset split to use
        length: Number of examples to fetch
        instance_id: Optional specific instance ID to fetch
        instance_ids: Optional list of instance IDs to fetch
        repo: Optional specific repo to fetch

    Returns:
        List of SweBenchExample objects
    """
    # Load the dataset with caching enabled
    if isinstance(dataset, SWEBenchLiteSubset):
        if instance_ids:
            msg = "instance_ids is not supported for lite subsets. Please pass a list of instance IDs instead."
            raise ValueError(msg)
        swe_bench_dataset = load_dataset(SWEBenchDataset.LITE.value, download_mode="reuse_dataset_if_exists")
        instance_ids = LITE_SUBSETS[dataset]
    else:
        swe_bench_dataset = load_dataset(dataset.value, download_mode="reuse_dataset_if_exists")

    # Get the requested split
    split_data = swe_bench_dataset[split]

    # Convert to SweBenchExample objects
    examples = []
    for row in split_data:
        if instance_id and row["instance_id"] != instance_id:
            continue
        if repo and row["repo"] != repo:
            continue
        if instance_ids and row["instance_id"] not in instance_ids:
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
            difficulty=get_difficulty(row["instance_id"]),
        )
        examples.append(example)

    if length:
        examples = examples[:length]

    return examples
