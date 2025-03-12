"""This is the harness for running an AI agent on the SWE Bench dataset."""

#!/usr/bin/env python
import json
import pprint
import random
import subprocess
import sys
from pathlib import Path

import lox

from codegen import Codebase
from codegen.agents.code_agent import CodeAgent
from codegen.configs.models.codebase import CodebaseConfig
from codegen.extensions.swebench.utils import (
    SweBenchExample,
    get_swe_bench_examples,
    load_predictions,
)

PARENT_DIR = Path(__file__).parent

PREDS_DNAME = PARENT_DIR / "predictions"


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


def run_agent_on_entry(entry: SweBenchExample, model: str, codebase: Codebase | None = None, run_id: str | None = None):
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

    if codebase is None:
        config = CodebaseConfig(
            disable_file_parse=True,  # Disable the graph AND disable file parsing (file.edit only)
        )
        codebase = Codebase.from_repo(repo_full_name=entry.repo, commit=base_commit, language="python", config=config)  # check out the repo

    metadata = {"run_id": run_id, "instance_id": instance_id, "difficulty": f"difficulty_{entry.difficulty}"}
    tags = [str(value) for value in metadata.values()]
    agent = CodeAgent(codebase=codebase, tags=tags, metadata=metadata)

    pprint.pprint(instance_id)
    pprint.pprint(gold_files)

    message = """Below is a real GitHub issue from a popular GitHub repository.
The issue was filed some time ago.
The repo has been checked out at the commit that existed at the moment the issue was filed.
If you are already familiar with this repo, be cautious!
You are working with an old version of the repo!
Filenames, directory names, file contents, etc may be different than what you're used to.

Propose changes to update the repo to fix the problem below.
*** IMPORTANT: *** DO NOT MODIFY ANY TESTS!
*** IMPORTANT: *** DO NOT ADD ANY TESTS!

Before commiting to do any modifications, double check your work with the Reflection tool.
you can also use that tool to check your work after you think you are done.
if you ever get stuck using other tools, use the Reflection tool to re asses your situation.
after every file edit, use the Reflection tool to check your work and sanity check yourself.
after editing a file you need to double check your work and use the ViewFiles tool to make sure you didn't break anything and that your edits are indeed correct.

You should follow the advices of the Reflection tool when ever they seem reasonable.

Also DO NOT ADD OR EDIT ANY TESTS!

"""
    message += problem_statement

    try:
        result = agent.run(prompt=message)
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

    # Did we get a successful patch?
    if not model_patch:
        pprint.pprint("=" * 60)
        pprint.pprint("Failed to generate a patch")
        pprint.pprint("=" * 60)

    return result


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
        process_one_instance_lox = lox.process(threads)(run_agent_on_entry)
        process_one_instance_func = process_one_instance_lox.scatter
        gather = process_one_instance_lox.gather
    else:
        process_one_instance_func = run_agent_on_entry

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
    dataset = {example.instance_id: example for example in get_swe_bench_examples()}
    process_instances(dataset, threads=10)


if __name__ == "__main__":
    status = main()
    sys.exit(status)
