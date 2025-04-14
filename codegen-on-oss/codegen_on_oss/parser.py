import gc
import sys
from pathlib import Path
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from codegen import Codebase
from codegen.sdk.codebase.validation import (
    PostInitValidationStatus,
    post_init_validation,
)
from codegen.sdk.extensions.utils import uncache_all
from loguru import logger

from codegen_on_oss.errors import PostValidationError
from codegen_on_oss.metrics import MetricsProfiler

if TYPE_CHECKING:
    from codegen.sdk.codebase.config import ProjectConfig


class CodegenParser:
    if TYPE_CHECKING:
        repo_dir: Path
        metrics_profiler: MetricsProfiler

    def __init__(self, repo_dir: Path, metrics_profiler: MetricsProfiler):
        self.repo_dir = repo_dir
        self.repo_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_profiler = metrics_profiler
        sys.setrecursionlimit(10000000)

    def parse(
        self, url: str, language: str | None = None, commit_hash: str | None = None
    ):
        """
        Parse the repository at the given URL. MetricsProfiler is used to profile the parse and
        post_init_validation.

        Args:
            url (str): The URL of the repository to parse.
            commit_hash (str | None): The commit hash to parse. If None, the head commit will be used.

        """
        repo_name = urlparse(url).path.removeprefix("/").removesuffix(".git")
        repo_dest_path = Path(*repo_name.split("/"))
        repo_dest_path = self.repo_dir / repo_dest_path
        repo_logger = logger.bind(repo_name=repo_name)

        self.gc()

        with self.metrics_profiler.start_profiler(
            name=repo_name, revision=commit_hash, language=language, logger=repo_logger
        ) as profile:
            # Awkward design here is due to adapting to using Codebase.from_repo() and parsing done in __init__.
            # May want to consider  __init__ with parsed state from a separate input handling / parser class.
            class ProfiledCodebase(Codebase):
                def __init__(self, *args, projects: "list[ProjectConfig]", **kwargs):
                    # Since Codebase is performing git ops, we need to extract commit if it wasn't explicitly provided.
                    profile.revision = (
                        profile.revision
                        or projects[
                            0
                        ].repo_operator.head_commit  # assume projects is not empty
                    )
                    # from_repo would have performed any repo initialization necessary
                    # It could pull or use cached
                    profile.reset_checkpoint()
                    super().__init__(*args, projects=projects, **kwargs)
                    profile.language = profile.language or str(self.language).lower()
                    profile.measure("codebase_parse")
                    validation_status = post_init_validation(self)

                    profile.measure("post_init_validation")
                    if validation_status is PostInitValidationStatus.SUCCESS:
                        return
                    else:
                        raise PostValidationError(validation_status)

            ProfiledCodebase.from_repo(
                repo_name, tmp_dir=str(self.repo_dir.absolute()), commit=commit_hash
            )

    def gc(self):
        uncache_all()
        gc.collect()
