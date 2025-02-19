#!/usr/bin/env python

import json
import os
import random
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from pprint import pprint


from tests import remove_patches_to_tests, run_tests
from utils import (
    FULL_DATASET_FNAME,
    choose_predictions,
    get_dataset,
    load_predictions,
)

using_dataset = "lite"

NUM_EVAL_PROCS = 5

def run_evals(swe_bench_tasks, log_dir, predictions_jsonl):
    run_evals_cmd = f"""
python -m swebench.harness.run_evaluation
    --predictions_path {predictions_jsonl}
    --max_workers 32
    --run_id {log_dir.replace('/', '-')}
    --dataset_name princeton-nlp/SWE-bench_Lite
    --cache_level instance
    --report_dir {log_dir}
"""
    run_evals_cmd = " ".join([line.strip() for line in run_evals_cmd.split() if line.strip()])
    print("Running evaluation command:", run_evals_cmd)

    subprocess.run(run_evals_cmd.split(), check=True)


def get_report(swe_bench_tasks, log_dir, predictions_jsonl, model_name_or_path):
    # Load and parse the evaluation results directly from the predictions file
    results = defaultdict(list)
    
    with open(predictions_jsonl) as f:
        for line in f:
            pred = json.loads(line)
            instance_id = pred['instance_id']
            
            # Track basic stats
            results['generated'].append(instance_id)
            
            # Check for evaluation logs
            log_file = Path(log_dir) / f"{instance_id}.eval.log"
            if log_file.exists():
                results['with_logs'].append(instance_id)
                log_content = log_file.read_text()
                
                if "PASS" in log_content:
                    results['resolved'].append(instance_id)
                    results['applied'].append(instance_id)
                elif "FAIL" in log_content:
                    results['applied'].append(instance_id)
                else:
                    results['no_apply'].append(instance_id)
            else:
                results['no_logs'].append(instance_id)

    # Convert lists to sets for compatibility with existing code
    return {k: set(v) for k, v in results.items()}


def update_pred_json(predictions, report):
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
            json_fname = Path("predictions/results") / f"{instance_id}.json"
        else:
            json_fname = pred["json_fname"]
            del save["json_fname"]  # Remove from save data if it exists
            
        Path(json_fname).write_text(json.dumps(save, indent=4))

    return predictions


def preds_to_jsonl(dname, predictions):
    dname = Path(dname)

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


def run_evals_on_dname(dname):
    dname = Path(dname)

    predictions = load_predictions([dname], devin_only=(using_dataset == "devin"))

    predictions_jsonl = preds_to_jsonl(dname, predictions)
    pprint(predictions_jsonl)

    log_dir = Path("logs") / dname.name
    log_dir.mkdir(exist_ok=True, parents=True)
    pprint(log_dir)

    any_need_evals = any("resolved" not in pred for pred in predictions.values())
    any_need_evals = True
    if any_need_evals:
        run_evals(FULL_DATASET_FNAME, str(log_dir), predictions_jsonl)

        model_name_or_path = list(predictions.values())[0]["model_name_or_path"]
        report = get_report(FULL_DATASET_FNAME, log_dir, predictions_jsonl, model_name_or_path)
        predictions = update_pred_json(predictions, report)

    return predictions_jsonl, log_dir


def combine_jsonl_logs(predictions, model_name_or_path):
    logs = Path("logs")
    log_dir = logs / model_name_or_path

    log_dir.mkdir(exist_ok=True)
    pprint(log_dir)

    preds_dir = Path("predictions") / model_name_or_path

    predictions_jsonl = preds_to_jsonl(preds_dir, predictions)
    for inst, pred in predictions.items():
        from_fname = logs / pred["dname"]
        # dump(from_fname, inst)
        from_fname = list(from_fname.glob(f"{inst}.*.log"))
        assert len(from_fname) <= 1, from_fname
        if not len(from_fname):
            print("Missing", pred["dname"], inst)
            continue
        from_fname = from_fname[0]
        # dump(from_fname)

        to_fname = log_dir / f"{inst}.{model_name_or_path}.eval.log"
        # dump(from_fname, to_fname)
        shutil.copyfile(from_fname, to_fname)

    return predictions_jsonl, log_dir


def main():
    # Automatically find all JSON files in predictions/results
    results_dir = Path("predictions/results")
    if not results_dir.exists():
        print(f"Directory does not exist: {results_dir}")
        return 1

    prediction_files = list(results_dir.glob("*.json"))
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

    print(f"Successfully loaded {len(predictions)} predictions")
    
    if predictions:
        # Create predictions JSONL file
        predictions_jsonl = preds_to_jsonl("predictions/results", predictions)
        print(f"\nCreated predictions JSONL: {predictions_jsonl}")

        # Setup log directory
        log_dir = Path("logs/results")
        log_dir.mkdir(exist_ok=True, parents=True)
        print(f"Using log directory: {log_dir}")

        # Run evaluations
        run_evals(FULL_DATASET_FNAME, str(log_dir), predictions_jsonl)

        # Get and display report
        model_name = "results"  # or whatever model name you want to use
        report = get_report(FULL_DATASET_FNAME, log_dir, predictions_jsonl, model_name)
        
        print("\nEvaluation Results:")
        print(f"Total predictions: {len(predictions)}")
        print(f"Successfully applied: {len(report.get('applied', []))}")
        print(f"Resolved: {len(report.get('resolved', []))}")
        print(f"Failed to apply: {len(report.get('no_apply', []))}")
        print(f"With logs: {len(report.get('with_logs', []))}")
        print(f"No logs: {len(report.get('no_logs', []))}")
        
        # Update prediction JSONs with results
        predictions = update_pred_json(predictions, report)
    else:
        print("No valid predictions found")
        return 1

    return 0


def stats_on_tests_before_and_after(report, predictions):
    num = 0
    num_before_pass = 0
    num_pass_to_fail = 0

    dataset = get_dataset()

    random.shuffle(predictions)

    outcomes = defaultdict(int)
    for pred in predictions:
        instance_id = pred["instance_id"]

        # if instance_id not in has_patch_not_resolved:
        #    continue

        num += 1

        entry = dataset[instance_id]
        before_passed, _ = run_tests(entry)
        if not before_passed:
            continue

        after_passed, _ = run_tests(entry, model_patch=pred["model_patch"])

        resolved = instance_id in report["resolved"]
        pprint(before_passed, after_passed, resolved)
        outcome = (before_passed, after_passed, resolved)
        outcomes[outcome] += 1
        pprint(sorted(outcomes.items()))

        if before_passed:
            num_before_pass += 1
        if before_passed and not after_passed:
            num_pass_to_fail += 1

        print()
        pprint(num)
        pprint(num_before_pass)
        pprint(num_pass_to_fail)

        pct_before_pass = num_before_pass / num * 100
        pprint(pct_before_pass)
        pct_pass_to_fail = num_pass_to_fail / num_before_pass * 100
        pprint(pct_pass_to_fail)

        print()


if __name__ == "__main__":
    sys.exit(main())
