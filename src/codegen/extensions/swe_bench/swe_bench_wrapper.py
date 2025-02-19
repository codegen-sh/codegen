import shutil
from collections.abc import Generator
from typing import Any

from datasets import load_dataset

from codegen.extensions.swe_bench.utils import NO_ENV_SETUP, SWEBenchEntry, SWEBenchEnvSetup, SWEBenchSplit, construct_codebase
from codegen.sdk.core.codebase import Codebase


class SWEBenchWrapper:
    def __init__(self, remove_after_run: bool = False):
        print("Loading SWE-bench dataset...")
        self.ds = load_dataset("princeton-nlp/SWE-bench")
        print("SWE-bench dataset loaded.")
        self.remove_after_run = remove_after_run
        self.repo_groups = self.create_repo_groups()

    def create_repo_groups(self) -> dict:
        # Create a list of all possible splits
        SPLITS: list[SWEBenchSplit] = ["train", "dev", "test"]

        # Create a nested dictionary with explicit type hints
        repo_groups: dict[SWEBenchSplit, dict[str, dict[str, list[Any]]]] = {}

        # Group entries from all splits
        for split in SPLITS:
            repo_groups[split] = {}
            for entry in self.ds[split]:
                repo = entry["repo"]
                environment_setup_commit = entry["environment_setup_commit"]

                # Initialize nested dictionaries if they don't exist
                if repo not in repo_groups[split]:
                    repo_groups[split][repo] = {}
                if environment_setup_commit not in repo_groups[split][repo]:
                    repo_groups[split][repo][environment_setup_commit] = []

                repo_groups[split][repo][environment_setup_commit].append(entry)

        return repo_groups

    def get_entries_for_split(self, split: SWEBenchSplit) -> Generator[tuple[SWEBenchEnvSetup | SWEBenchEntry, Codebase], None, None]:
        # ===== [ For each repo in the split ] =====
        for repo in self.repo_groups[split]:
            # construct the codebase for the repo
            codebase = construct_codebase(repo_full_name=repo)
            # ===== [ For each environment setup commit ] =====
            for environment_setup_commit in self.repo_groups[split][repo]:
                # yield the environment setup commit
                if environment_setup_commit:
                    #  no need to parse the codebase on the environment commit
                    codebase.checkout(commit=environment_setup_commit, remote=True)
                    yield SWEBenchEnvSetup(split=split, environment_setup_commit=environment_setup_commit), codebase
                else:
                    yield SWEBenchEnvSetup(split=split, environment_setup_commit=NO_ENV_SETUP), codebase
                # ===== [ For each test setup commit ] =====
                for entry in self.repo_groups[split][repo][environment_setup_commit]:
                    codebase.checkout(commit=entry["base_commit"], remote=True)
                    # yield the test entry with a parsed codebase object
                    yield SWEBenchEntry(entry=entry, split=split), codebase

        if codebase and self.remove_after_run:
            # remove the repo from the tmp_dir
            shutil.rmtree(f"/tmp/codegen/{repo}")


if __name__ == "__main__":
    swe_bench_wrapper = SWEBenchWrapper()
    for entry, codebase in swe_bench_wrapper.get_entries_for_split("train"):
        if isinstance(entry, SWEBenchEnvSetup):
            print(f"Environment setup commit: {entry.environment_setup_commit}")
            # install dependencies...
        elif isinstance(entry, SWEBenchEntry):
            print(f"Entry: {entry.entry['instance_id']}")
            problem_statement = entry.entry["problem_statement"]
            print(f"Task: {problem_statement[:20]}")
            # send of agent to solve tasks....

        print(f"Number of files: {len(codebase.files)}")
