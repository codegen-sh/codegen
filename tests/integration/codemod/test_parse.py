# TODO: SCRUB
import logging
import os

import psutil
import pytest

from codegen.configs.models.codebase import CodebaseConfig
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.sdk.codebase.config import ProjectConfig
from codegen.sdk.codebase.validation import PostInitValidationStatus, post_init_validation
from codegen.sdk.core.codebase import Codebase
from tests.shared.codemod.models import Repo
from tests.shared.utils.recursion import set_recursion_limit

BYTES_IN_GIGABYTE = 1024**3
MAX_ALLOWED_GIGABYTES = 31
logger = logging.getLogger(__name__)


@pytest.mark.timeout(60 * 12, func_only=True)
def test_codemods_parse(repo: Repo, op: RepoOperator, request) -> None:
    # Setup Feature Flags
    sync = request.config.getoption("sync-graph").lower() == "true"
    log_parse = request.config.getoption("log-parse").lower() == "true"
    if repo.config is not None:
        codebase_config = repo.config
    else:
        codebase_config = CodebaseConfig()

    codebase_config = codebase_config.model_copy(update={"verify_graph": sync, "debug": log_parse, "ignore_process_errors": False})

    set_recursion_limit()
    # Setup Codebase
    projects = [ProjectConfig(repo_operator=op, programming_language=repo.language, subdirectories=repo.subdirectories)]
    codebase = Codebase(projects=projects, config=codebase_config)
    process = psutil.Process(os.getpid())
    memory_used = process.memory_info().rss
    logger.info(f"Using {memory_used / BYTES_IN_GIGABYTE} GB of memory.")
    assert memory_used <= BYTES_IN_GIGABYTE * MAX_ALLOWED_GIGABYTES, "Graph is using too much memory!"
    validation_res = post_init_validation(codebase)
    if validation_res != PostInitValidationStatus.SUCCESS:
        msg = f"Graph failed post init validation: {validation_res}!"
        raise Exception(msg)
