from typing import Literal

from pydantic import BaseModel

from codegen.git.repo_operator.remote_repo_operator import RemoteRepoOperator
from codegen.git.schemas.repo_config import RepoConfig
from codegen.sdk.codebase.config import ProjectConfig
from codegen.sdk.core.codebase import Codebase, PyCodebaseType

# Define the SWEBenchSplit type using Literal
SWEBenchSplit = Literal["train", "dev", "test"]
NO_ENV_SETUP = "NO_ENV_SETUP"


class SWEBenchEnvSetup(BaseModel):
    split: SWEBenchSplit
    environment_setup_commit: str = NO_ENV_SETUP


class SWEBenchEntry(BaseModel):
    split: SWEBenchSplit
    entry: dict


def construct_codebase(repo_full_name: str) -> PyCodebaseType:
    repo_name = repo_full_name.split("/")[-1]
    repo_config = RepoConfig(name=repo_name, full_name=repo_full_name, base_dir="/tmp/codegen")

    # clone or pull the repo
    print(f"Cloning or pulling {repo_full_name}...")
    remote_operator = RemoteRepoOperator(repo_config=repo_config, bot_commit=False)
    print(f"Cloned or pulled {repo_full_name}.")

    # create the project config
    projects = [ProjectConfig(repo_operator=remote_operator, base_path=None, subdirectories=None)]

    # parse the codebase
    print("Parsing codebase...")
    codebase = Codebase(projects=projects)
    print("Codebase parsed.")

    return codebase
