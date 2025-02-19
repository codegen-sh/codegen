import datetime
import json
import shutil
from pathlib import Path
from pprint import pprint

from datasets import load_dataset


FULL_DATASET = "princeton-nlp/SWE-bench"
FULL_DATASET_FNAME = FULL_DATASET.replace("/", "--") + ".json"


VERIFIED_DATASET = "princeton-nlp/SWE-bench-verified"
VERIFIED_DATASET_FNAME = VERIFIED_DATASET.replace("/", "--") + ".json"

LITE_DATASET = "princeton-nlp/SWE-bench_Lite"
LITE_DATASET_FNAME = LITE_DATASET.replace("/", "--") + ".json"


def dump_dataset(dataset, fname):
    """
    Save the dataset to json.
    """
    entries = list(dataset)
    for entry in entries:
        entry["FAIL_TO_PASS"] = json.loads(entry["FAIL_TO_PASS"])
        entry["PASS_TO_PASS"] = json.loads(entry["PASS_TO_PASS"])

    with open(fname, "w") as f:
        json.dump(entries, f, indent=4)


def get_full_dataset():
    return get_dataset(FULL_DATASET, FULL_DATASET_FNAME)


def get_lite_dataset():
    return get_dataset(LITE_DATASET, LITE_DATASET_FNAME)


def get_verified_dataset():
    return get_dataset(VERIFIED_DATASET, VERIFIED_DATASET_FNAME)


def get_dataset(dataset, fname):
    """
    Load the `DATASET` from hugging face, and turn it into a dict
    keyed on `instance_id`.
    Cache the dict locally in a json file.
    """

    fname = Path(fname)
    if fname.exists():
        dataset = json.loads(fname.read_text())
    else:
        pprint(dataset)
        dataset = load_dataset(dataset)
        dataset = dataset["test"]
        dump_dataset(dataset, fname)
        pprint(dataset)

    res = dict()
    for entry in dataset:
        res[entry["instance_id"]] = entry

    return res


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


def is_plausible(pred):
    attrs = "model_patch edit_outcome lint_outcome test_outcome".split()
    for attr in attrs:
        if not pred.get(attr):
            return
    return True


def get_plausible(preds):
    return set(inst for inst, pred in preds.items() if is_plausible(pred))


def check_criteria(pred, criteria):
    attrs = criteria.split()
    for attr in attrs:
        if not pred[attr]:
            return False
    return True


def pick_winner(results):
    """
    Given that we didn't obtain a result with all good outcomes,
    try a series of weaker outcome sets to find the strongest result.
    """
    priority = (
        "model_patch edit_outcome lint_outcome test_outcome",  # all good!
        "model_patch edit_outcome lint_outcome",  # all good but test_outcome
        "model_patch lint_outcome",  # a patch that lints?
        "model_patch edit_outcome",  # a patch that had no edit errors?
        "model_patch",  # anything with an actual patch!
    )

    # choose the best result available
    for criteria in priority:
        for res in results:
            if check_criteria(res, criteria):
                return res

    # choose the first result as a last resort
    if results:
        return results[0]


def choose_pred(inst, all_preds, dnames):
    results = []
    for i in range(len(all_preds)):
        preds = all_preds[i]
        dname = dnames[i]

        if inst not in preds:
            continue
        pred = dict(preds[inst])
        pred["dname"] = Path(dname).name
        results.append(pred)

    return pick_winner(results)


def choose_predictions(dnames, model_name_or_path=None, copy_md=False, devin_only=False):
    all_preds = [load_predictions([dname], devin_only=devin_only) for dname in dnames]
    all_instances = set()
    for preds in all_preds:
        all_instances.update(preds.keys())

    chosen = dict()
    for inst in all_instances:
        res = choose_pred(inst, all_preds, dnames)
        chosen[inst] = res

        if copy_md:
            pred_dname = Path("predictions")
            md_fname = pred_dname / res["dname"] / (inst + ".md")
            assert md_fname.exists(), md_fname
            new_md_fname = pred_dname / model_name_or_path / (inst + ".md")
            shutil.copyfile(md_fname, new_md_fname)

    for inst in chosen:
        pred = dict(chosen[inst])
        pred["model_name_or_path"] = model_name_or_path
        chosen[inst] = pred

    pprint(len(chosen))
    pprint(chosen)
    return chosen
