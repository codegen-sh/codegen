"""This is the harness for running an AI agent on the SWE Bench dataset."""

#!/usr/bin/env python
import json
import pprint
import random
import subprocess
import sys

import lox

from codegen import Codebase

# coding agent
from codegen.agents.code_agent import CodeAgent
from codegen.extensions.langchain.utils import SweBenchExample, get_swe_bench_examples
from codegen.extensions.swebench.constants import PREDS_DNAME

# Replace the dump import with pprint
# from dump import dump
# from tests import run_tests
from codegen.extensions.swebench.utils import (
    get_full_dataset,  # noqa: F401
    load_predictions,
)


def diff_versus_commit(git_dname, commit):
    """Take a diff of `git_dname` current contents versus the `commit`."""
    diff_cmd = f"git -C {git_dname} diff {commit}"
    diff_output = subprocess.check_output(diff_cmd.split()).decode()
    return diff_output


def files_in_patch(patch):
    """Extract the list of modified files from a unified diff patch string."""
    files = []
    for line in patch.split("\n"):
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            fname = line.split("/", 1)[1]
            if fname not in files:
                files.append(fname)
    return files


def show_problems(dataset):
    """Print out all the instance_id and problem_descriptions."""
    for inst, entry in dataset.items():
        problem = entry.problem_statement.splitlines()[0]
        print(f"{inst}: {problem}")


def process_one_instance(entry: SweBenchExample):
    """Process one `entry` from SWE Bench using the LLM `models` at the
    given `temperature`.  Set `model_name_or_path` in the result json.
    """
    instance_id = entry.instance_id
    base_commit = entry.base_commit

    print("=" * 60)
    pprint.pprint(instance_id)
    print("=" * 60)
    problem_statement = entry.problem_statement
    print(problem_statement)

    gold_files = files_in_patch(entry.patch)

    results = []
    cost = 0
    winner = None

    codebase = Codebase.from_repo(repo_full_name=entry.repo, commit=base_commit, language="python")  # check out the repo

    agent = CodeAgent(codebase=codebase)

    pprint.pprint(instance_id)
    pprint.pprint(gold_files)

    message = """Below is a real GitHub issue from a popular GitHub repository.
The issue was filed some time ago.
The repo has been checked out at the commit that existed at the moment the issue was filed.
If you are already familiar with this repo, be cautious!
You are working with an old version of the repo!
Filenames, directory names, file contents, etc may be different than what you're used to.

Propose changes to update the repo to fix the problem below.

"""
    message += problem_statement

    try:
        result = agent.run(prompt=message, session_id="swebench")
    except Exception as agent_error:
        pprint.pprint(f"Instance ID: {instance_id} terminated with error: {agent_error}")
        raise agent_error

    # Get the diff between the current state and the original commit
    model_patch = codebase.get_diff(base=base_commit)
    pprint.pprint(model_patch)

    # Record the results for the logs
    result = dict(
        # Required args for running eval tests
        instance_id=instance_id,
        model_patch=model_patch,
        # For computing stats
        gold_files=gold_files,
        edited_files=files_in_patch(model_patch),
    )
    results.append(result)

    pprint.pprint(result)

    # Did we get a successful patch?
    if model_patch:
        winner = result

    # If there's no clear winner, look for the most viable result we got...
    if not winner:
        msg = "No winner found"
        raise ValueError(msg)

    # Avoid circular reference when we save to json
    winner = dict(winner)

    winner.update(
        dict(
            all_results=results,  # Record all the results for later analysis
            cost=cost,  # total cost across all results
        )
    )

    return winner


def process_instances(dataset: dict[str, SweBenchExample], threads: int):
    """Dataset - The subset of the SWE Bench dataset to process.
    threads - How many problems to attempt concurrently.
    prior_dnames - Names of predictions/ dirnames from previous runs.
                   If they contain a plausible solution for an instance,
                   don't continue looking.
    """
    # Create the predictions directory if it doesn't exist
    PREDS_DNAME.mkdir(exist_ok=True)
    out_dname = PREDS_DNAME / "results"
    out_dname.mkdir(exist_ok=True)

    pprint.pprint(out_dname)

    # If we are restarting this run, figure out which instances are already done.
    done_preds = load_predictions([out_dname])
    done_instances = set(done_preds.keys())
    pprint.pprint(len(done_instances))

    all_instances = set(dataset.keys())

    remaining_instances = set(all_instances)
    remaining_instances -= done_instances

    remaining_instances = list(remaining_instances)
    random.shuffle(remaining_instances)

    pprint.pprint(sorted(remaining_instances))
    pprint.pprint(len(remaining_instances))

    print()
    print("press enter...")
    input()

    if threads > 1:
        process_one_instance_lox = lox.process(threads)(process_one_instance)
        process_one_instance_func = process_one_instance_lox.scatter
        gather = process_one_instance_lox.gather
    else:
        process_one_instance_func = process_one_instance

    for instance_id in remaining_instances:
        if instance_id in done_instances:
            print("skipping", instance_id)
            continue

        result = process_one_instance_func(
            dataset[instance_id],
        )
        with open(out_dname / f"{instance_id}.json", "w") as f:
            json.dump(result, f)

        print("#" * 60)
        # input()

    if threads > 1:
        gather()


def main():
    # Load the SWE Bench dataset
    dataset = {}
    for example in get_swe_bench_examples():
        # codegen-sdk currently fails on this repo
        if example.repo == "django/django":
            continue
        dataset[example.instance_id] = example

    threads = 1

    process_instances(dataset, threads)


if __name__ == "__main__":
    status = main()
    sys.exit(status)
