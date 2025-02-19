"""
This is the harness for running an AI agent on the SWE Bench dataset.

"""

#!/usr/bin/env python

import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path
import datetime
import pprint

import lox

# Replace the dump import with pprint
# from dump import dump
# from tests import run_tests
from utils import get_full_dataset  # noqa: F401
from utils import get_lite_dataset  # noqa: F401
from utils import  get_plausible, load_predictions, pick_winner


# coding agent
from agent import create_codebase_agent
from codegen import Codebase


REPOS_DNAME = Path("repos")
CHAT_LOGS_DNAME = Path("chat-logs")
PREDS_DNAME = Path("predictions")


def diff_versus_commit(git_dname, commit):
    """
    Take a diff of `git_dname` current contents versus the `commit`.
    """

    diff_cmd = f"git -C {git_dname} diff {commit}"
    diff_output = subprocess.check_output(diff_cmd.split()).decode()
    return diff_output


def files_in_patch(patch):
    """
    Extract the list of modified files from a unified diff patch string.
    """
    files = []
    for line in patch.split("\n"):
        if line.startswith("--- a/") or line.startswith("+++ b/"):
            fname = line.split("/", 1)[1]
            if fname not in files:
                files.append(fname)
    return files


def checkout_repo(git_tempdir, entry):
    """
    Clone the SWE Bench entry's git `repo` into `dname` at the `base_commit`.
    Make a tempdir if no `dname` provided.
    """
    github_url = "https://github.com/"
    repo_url = github_url + entry["repo"]
    commit = entry["base_commit"]

    print(repo_url, commit)

    checkout_repo_url_commit(git_tempdir, repo_url, commit)


def checkout_repo_url_commit(repo_dname, url, commit):
    """
    Clone the git `url` into `dname` at `commit`.
    Check a local cache of the bare repo to avoid pulling from github every time.
    """

    # Extract repo name from URL
    repo_name = url.split("/")[-1].split(".")[0]
    repo_name += ".git"

    # dump(repo_name)
    pprint.pprint(repo_name)
    REPOS_DNAME.mkdir(exist_ok=True)
    bare_repo = REPOS_DNAME / repo_name

    if not bare_repo.exists():
        cmd = f"git clone --bare {url} {bare_repo}"
        subprocess.run(cmd.split(), check=True)

    cmd = f"git clone {bare_repo} {repo_dname}"
    subprocess.run(cmd.split(), check=True)

    cmd = f"git -c advice.detachedHead=false -C {repo_dname} checkout {commit}"
    subprocess.run(cmd.split(), check=True)


def show_problems(dataset):
    """
    Print out all the instance_id and problem_descriptions.
    """
    for inst, entry in dataset.items():
        problem = entry["problem_statement"].splitlines()[0]
        print(f"{inst}: {problem}")


def run_pre_existing_tests(entry, git_dname):
    """Given the current contents of the `git_dname`, run the tests that
    were present in the entry's `repo` at the time of the
    `base_commit` or which have been added into the repo since.  This
    checks if the code in the `git_dname` has broken pre-existing
    tests or is failing any newly added tests.

    It does NOT attempt to run the tests in the `test_patch` which
    are used to evaluate whether the `model_patch` has resolved the
    `problem_statement`.

    Returns None if all the tests passed. Returns the text of the
    test run output if any failed.
    """

    model_patch = diff_versus_commit(git_dname, entry["base_commit"])
    # passed, output = run_tests(
    #     entry,
    #     model_patch=model_patch,
    #     use_test_patch=False,
    # )
    # We were UNABLE to run tests
    # if passed is None:
    #     return

    # if passed:
    #     return

    # Just keep the output after the (no-op) test patch applied,
    # which is the actual output from the tests that were run.
    # output = output.split(">>>>> Applied Patch (test)")[-1]

    # return output




def process_one_instance(entry, out_dname):
    """Process one `entry` from SWE Bench using the LLM `models` at the
    given `temperature`.  Set `model_name_or_path` in the result json.
    Store the result json and the chat log into `out_dname`.
    """

    instance_id = entry["instance_id"]
    base_commit = entry["base_commit"]

    print("=" * 60)
    pprint.pprint(instance_id)
    print("=" * 60)
    problem_statement = entry["problem_statement"]
    print(problem_statement)

    ###
    # DO NOT assist aider by telling it which files need to be modified!
    oracle = False
    gold_files = files_in_patch(entry["patch"])
    if oracle:
        oracle_files = gold_files
    else:
        oracle_files = None
    ###


    results = []
    cost = 0
    winner = None

    num_tries = 1
    # Do NUM_TRIES tries for each of the models, until we find a *plausible* solution
    for attempt in range(1, num_tries + 1):
            codebase = Codebase.from_repo(
                repo_full_name=entry["repo"],
                commit=entry["base_commit"],
                language="python"
            ) # check out the repo

            agent = create_codebase_agent(
                codebase=codebase,
                model_name="gpt-4o",
                temperature=0,
                verbose=True
            )
            
            # for usage for testing for the model
            # test_cmd = lambda: run_pre_existing_tests(entry, codebase.repo_path)  # noqa: E731

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
                result = agent.invoke(
                    {"input": message},
                    config={"configurable": {"session_id": "demo"}}
                )
            except Exception as coder_err:
                # swallow any exceptions during benchmarking
                pprint.pprint(coder_err)
                continue


            pprint.pprint(instance_id)
            pprint.pprint(gold_files)


            # Get the diff between the current state and the original commit
            model_patch = diff_versus_commit(codebase.repo_path, base_commit)
            pprint.pprint(model_patch)

            # Record the results for the logs
            result = dict(
                # Required args for running eval tests
                instance_id=instance_id,
                model_patch=model_patch,
                # For computing stats
                gold_files=gold_files,
                edited_files=files_in_patch(model_patch)
            )
            result["try"] = attempt  # `try` is a python keyword
            results.append(result)

            pprint.pprint(result)

            # Did we get a successful edit, lint and test? If so, we found a plausible solution!
            if model_patch:
                winner = result
                break


    # If there's no clear winner, look for the most viable result we got...
    if not winner:
        winner = pick_winner(results)

    if not winner:
        result = dict(
            # Required args for running eval tests
            instance_id=instance_id,
            model_patch=None,
        )

    pprint.pprint(winner)
    if not winner:
        return

    print("\n\nFinal diff:\n")
    print(winner["model_patch"])

    # Avoid circular reference when we save to json
    winner = dict(winner)

    winner.update(
        dict(
            tries=attempt,
            all_results=results,  # Record all the results for later analysis
            cost=cost,  # total cost across all results
        )
    )

    out_fname = out_dname / (instance_id + ".json")
    out_fname.write_text(json.dumps(winner, indent=4))


def process_instances(
    dataset, threads, prior_dnames
):
    """
    dataset - The subset of the SWE Bench dataset to process.
    threads - How many problems to attempt concurrently.
    prior_dnames - Names of predictions/ dirnames from previous runs.
                   If they contain a plausible solution for an instance,
                   don't continue looking.
    """

    # Create the predictions directory if it doesn't exist
    PREDS_DNAME.mkdir(exist_ok=True)
    out_dname = PREDS_DNAME / "results"
    out_dname.mkdir()

    pprint.pprint(out_dname)

    # If we are restarting this run, figure out which instances are already done.
    done_preds = load_predictions([out_dname])
    done_instances = set(done_preds.keys())
    pprint.pprint(len(done_instances))

    pprint.pprint(prior_dnames)
    prior_preds = load_predictions(prior_dnames)
    pprint.pprint(len(prior_preds))

    plausible_instances = get_plausible(prior_preds)
    pprint.pprint(len(plausible_instances))

    if prior_preds:
        # Just keep trying to solve instances that exist in the previous runs
        all_instances = set(prior_preds.keys())
    else:
        all_instances = set(dataset.keys())

    remaining_instances = set(all_instances)
    remaining_instances -= done_instances
    remaining_instances -= plausible_instances

    remaining_instances = list(remaining_instances)
    random.shuffle(remaining_instances)

    pprint.pprint(sorted(remaining_instances))
    pprint.pprint(len(remaining_instances))

    print()
    print("press enter...")
    input()

    if not CHAT_LOGS_DNAME.exists():
        CHAT_LOGS_DNAME.mkdir()

    chat_history_dname = CHAT_LOGS_DNAME / "results"
    chat_history_dname.mkdir(exist_ok=True)

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

        process_one_instance_func(
            dataset[instance_id],
            out_dname,
        )

        print("#" * 60)
        # input()

    if threads > 1:
        gather()


def main():

    # Load the SWE Bench dataset
    # dataset = get_full_dataset()
    # dataset = get_verified_dataset()
    dataset = get_lite_dataset()
    threads = 10

    # Any predictions/ dirs provided on the command line are treated
    # as earlier, higher priority runs.  If a plausible solution was
    # found for an instance already, we don't need to keep looking in
    # this run.
    prior_dnames = sys.argv[1:]

    process_instances(
        dataset, threads, prior_dnames
    )


if __name__ == "__main__":
    status = main()
    sys.exit(status)
