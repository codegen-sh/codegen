import shutil
import subprocess
from pathlib import Path

import codegen
from codegen import Codebase
from codegen.sdk.core.detached_symbols.function_call import FunctionCall
from codegen.shared.configs.models.feature_flags import CodebaseFeatureFlags


def should_process_join_call(call, soft_delete_models, join_methods):
    """Determine if a function call should be processed for soft delete conditions."""
    if str(call.name) not in join_methods:
        return False

    call_args = list(call.args)
    if not call_args:
        return False

    model_name = str(call_args[0].value)
    return model_name in soft_delete_models


def add_deleted_at_check(file, call, model_name):
    """Add the deleted_at check to a join call."""
    call_args = list(call.args)
    deleted_at_check = f"{model_name}.deleted_at.is_(None)"

    if len(call_args) == 1:
        print(f"Adding deleted_at check to function call {call.source}")
        call_args.append(deleted_at_check)
        return

    second_arg = call_args[1].value
    if second_arg.source == deleted_at_check:
        print(f"Skipping {file.filepath} because the deleted_at check is already present")
        return

    if isinstance(second_arg, FunctionCall) and second_arg.name == "and_":
        if deleted_at_check in {str(x) for x in second_arg.args}:
            print(f"Skipping {file.filepath} because the deleted_at check is already present")
            return
        print(f"Adding deleted_at check to and_ call in {file.filepath}")
        second_arg.args.append(deleted_at_check)
    else:
        print(f"Adding deleted_at check to {file.filepath}")
        call_args[1].edit(f"and_({second_arg.source}, {deleted_at_check})")

    ensure_and_import(file)


def ensure_and_import(file):
    """Ensure the file has the necessary and_ import."""
    if not any("and_" in imp.name for imp in file.imports):
        print(f"File {file.filepath} does not import and_. Adding import.")
        file.add_import_from_import_string("from sqlalchemy import and_")


def clone_repo(repo_url: str, repo_path: Path) -> None:
    """Clone a git repository to the specified path."""
    if repo_path.exists():
        shutil.rmtree(repo_path)
    subprocess.run(["git", "clone", repo_url, str(repo_path)], check=True)


@codegen.function("sqlalchemy-soft-delete")
def process_soft_deletes(codebase):
    """Process soft delete conditions for join methods in the codebase."""
    soft_delete_models = {
        "User",
        "Update",
        "Proposal",
        "Comment",
        "Project",
        "Team",
        "SavedSession",
    }
    join_methods = {"join", "outerjoin", "innerjoin"}

    for file in codebase.files:
        for call in file.function_calls:
            if not should_process_join_call(call, soft_delete_models, join_methods):
                continue

            model_name = str(list(call.args)[0].value)
            print(f"Found join method for model {model_name} in file {file.filepath}")
            add_deleted_at_check(file, call, model_name)

    codebase.commit()
    print("commit")
    print(codebase.get_diff())


if __name__ == "__main__":
    from codegen.sdk.codebase.config import CodebaseConfig
    from codegen.sdk.core.codebase import Codebase

    repo_path = Path("/tmp/core")
    repo_url = "https://github.com/hasgeek/funnel.git"

    try:
        clone_repo(repo_url, repo_path)
        subprocess.run(["git", "-C", str(repo_path), "checkout", "8454e15"], check=True)
        codebase = Codebase(str(repo_path), language="python", config=CodebaseConfig(feature_flags=CodebaseFeatureFlags(disable_graph=True)))
        process_soft_deletes(codebase)
    finally:
        shutil.rmtree(repo_path)
