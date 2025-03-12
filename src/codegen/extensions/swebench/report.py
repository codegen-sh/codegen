#!/usr/bin/env python

import json
import subprocess
from collections import defaultdict
from pathlib import Path

from codegen.extensions.swebench.enums import SWEBenchDataset
from codegen.extensions.swebench.tests import remove_patches_to_tests

NUM_EVAL_PROCS = 5


def run_evals(predictions_jsonl, logs_dir: Path, dataset: SWEBenchDataset, run_id: str):
    """Run the evaluations on the predictions on modal."""
    run_evals_cmd = f"""
python -m swebench.harness.run_evaluation
    --predictions_path {predictions_jsonl}
    --run_id {run_id}
    --dataset_name {dataset.value}
    --cache_level instance
    --report_dir {logs_dir}
    --modal true
"""
    run_evals_cmd = " ".join([line.strip() for line in run_evals_cmd.split() if line.strip()])
    print("Running evaluation command:", run_evals_cmd)

    subprocess.run(run_evals_cmd.split(), check=True)


def get_report(predictions_jsonl, logs_dir: Path):
    # Load and parse the evaluation results directly from the predictions file
    results = defaultdict(list)

    with open(predictions_jsonl) as f:
        for line in f:
            pred = json.loads(line)
            instance_id = pred["instance_id"]

            # Track basic stats
            results["generated"].append(instance_id)

            # Check for evaluation logs
            log_file = logs_dir / f"{instance_id}.eval.log"
            if log_file.exists():
                results["with_logs"].append(instance_id)
                log_content = log_file.read_text()

                if "PASS" in log_content:
                    results["resolved"].append(instance_id)
                    results["applied"].append(instance_id)
                elif "FAIL" in log_content:
                    results["applied"].append(instance_id)
                else:
                    results["no_apply"].append(instance_id)
            else:
                results["no_logs"].append(instance_id)

    # Convert lists to sets for compatibility with existing code
    return {k: set(v) for k, v in results.items()}


def update_pred_json(predictions, report, predictions_dir: Path):
    all_instances = set(report.get("generated", []))
    all_instances.update(set(report.get("no_generation", [])))

    for instance_id, pred in predictions.items():
        # Use get() to handle missing 'resolved' key, defaulting to empty set
        was_resolved = instance_id in report.get("resolved", set())
        if "resolved" in pred and pred["resolved"] == was_resolved:
            continue

        assert instance_id in all_instances, instance_id

        pred["resolved"] = was_resolved
        save = dict(pred)

        # Construct json_fname if it doesn't exist
        if "json_fname" not in pred:
            json_fname = predictions_dir / f"{instance_id}.json"
        else:
            json_fname = pred["json_fname"]
            del save["json_fname"]  # Remove from save data if it exists

        Path(json_fname).write_text(json.dumps(save, indent=4))

    return predictions


def preds_to_jsonl(predictions, predictions_dir: Path):
    dname = predictions_dir

    predictions_jsonl = str(dname / "all_preds.jsonl")
    print(f"Creating JSONL file: {predictions_jsonl}")

    # Use a default model name since it's not in the predictions
    model_name = "results"

    with open(predictions_jsonl, "w") as fh:
        for inst, pred in predictions.items():
            minimal_pred = {
                "model_name_or_path": model_name,  # Use default model name
                "model_patch": remove_patches_to_tests(pred["model_patch"]) if "model_patch" in pred else pred.get("patch", ""),
                "instance_id": pred["instance_id"],
            }
            fh.write(json.dumps(minimal_pred) + "\n")
    return predictions_jsonl


def generate_report(predictions_dir: Path, logs_dir: Path, dataset: SWEBenchDataset, run_id: str):
    # Automatically find all JSON files in predictions/results
    if not predictions_dir.exists():
        print(f"Directory does not exist: {predictions_dir}")
        return 1

    predictions_jsonl = predictions_dir / "all_preds.jsonl"
    existing_preds = predictions_jsonl.exists()
    prediction_files = list(predictions_dir.glob("*.json"))
    print(f"Found {len(prediction_files)} prediction files")

    predictions = {}
    for file_path in prediction_files:
        try:
            with open(file_path) as f:
                prediction = json.load(f)
                if isinstance(prediction, dict) and "instance_id" in prediction:
                    predictions[prediction["instance_id"]] = prediction
        except json.JSONDecodeError:
            print(f"Error reading JSON from {file_path}")
            continue
    if not existing_preds:
        if not predictions:
            print("No valid predictions found")
            return 1

        print(f"Successfully loaded {len(predictions)} predictions")

        predictions_jsonl = preds_to_jsonl(predictions, predictions_dir)

    # Setup log directory
    log_dir = logs_dir / "results"
    log_dir.mkdir(exist_ok=True, parents=True)
    print(f"Using log directory: {log_dir}")

    # Run evaluations
    run_evals(predictions_jsonl, logs_dir, dataset, run_id)

    # Get and display report
    report = get_report(predictions_jsonl, logs_dir)

    # Update prediction JSONs with results
    predictions = update_pred_json(predictions, report, predictions_dir)

    return 0
