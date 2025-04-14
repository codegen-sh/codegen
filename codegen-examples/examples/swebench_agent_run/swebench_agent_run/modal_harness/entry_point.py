"""Largely copied from swebench/harness/modal_eval/run_evaluation_modal.py

Points of difference:
 - We added CGModalSandboxRuntime class that is used to populate the sandbox with the snapshot.
 - We are adding custom post-processing of the TestOutput in run_instances_modal
"""

import json
import time
import traceback
from contextlib import nullcontext
from typing import TYPE_CHECKING
from unittest.mock import patch

import modal as modal_lib
import tenacity
from swebench.harness.constants import (
    APPLY_PATCH_FAIL,
    APPLY_PATCH_PASS,
)
from swebench.harness.docker_build import setup_logger
from swebench.harness.grading import get_eval_report
from swebench.harness.modal_eval.run_evaluation_modal import (
    LOCAL_SANDBOX_ENTRYPOINT_PATH,
    REMOTE_SANDBOX_ENTRYPOINT_PATH,
    ModalSandboxRuntime,
    TestOutput,
    get_log_dir,
    swebench_image,
)
from swebench.harness.run_evaluation import main
from swebench.harness.test_spec.test_spec import TestSpec
from swebench.harness.utils import EvaluationError

if TYPE_CHECKING:
    from codegen.extensions.swebench.utils import SweBenchExample

image = (
    modal_lib.Image.debian_slim(python_version="3.13")
    .apt_install(["git", "ripgrep"])
    .add_local_dir(
        "../../../",
        "/root/codegen",
        ignore=[
            "__pycache__",
            "**/__pycache__",
            ".venv",
            "**/.venv",
            "tests",
            "**/tests",
            "codegen-on-oss/",
            "codegen-examples/",
            "build/",
            ".vscode/",
            ".codegen/",
            ".github/",
            ".architecture/",
            "docs/",
            "*cache/",
        ],
        copy=True,
    )
    .add_local_dir(
        ".",
        "/root/swebench_agent_run",
        ignore=[
            "__pycache__",
            "**/__pycache__",
            ".venv",
            "**/.venv",
            ".env*",
        ],
        copy=True,
    )
    .run_commands(
        "pip install -e /root/codegen",
        "rm -r /root/codegen/.git",
        "pip install -e /root/swebench_agent_run",
    )
)

app = modal_lib.App(
    name="swebench-agent-run", image=image, secrets=[modal_lib.Secret.from_dotenv()]
)


class ShouldRetry(Exception):
    pass


@app.function(timeout=43200, max_containers=10)
async def run_agent_modal(entry: "SweBenchExample", run_id: str, model: str):
    from codegen.extensions.swebench.harness import run_agent_on_entry

    """Modal function to process a single example from the SWE-bench dataset."""
    for attempt in tenacity.Retrying(
        wait=tenacity.wait_exponential_jitter(max=600),
        retry=tenacity.retry_if_exception_type(ShouldRetry),
    ):
        with attempt:
            try:
                return run_agent_on_entry(entry, run_id=run_id, model=model)
            except Exception as e:
                if any(
                    msg in str(e).lower()
                    for msg in (
                        "rate limit",
                        "too many requests",
                        "429",
                        "throttle",
                        "quota exceeded",
                        "capacity",
                        "limit exceeded",
                    )
                ):
                    raise ShouldRetry() from e
                else:
                    raise e


@app.function(
    image=swebench_image.add_local_file(
        LOCAL_SANDBOX_ENTRYPOINT_PATH, REMOTE_SANDBOX_ENTRYPOINT_PATH, copy=True
    ).add_local_python_source("eval_cli", "swebench_agent_run", copy=True),
    timeout=120 * 60,  # Much larger than default timeout to account for image build time
)
def run_instance_modal(
    test_spec: TestSpec,
    pred: dict,
    run_id: str,
    timeout: int | None = None,
) -> TestOutput:
    """Run a single instance with the given prediction.

    Args:
        test_spec (TestSpec): TestSpec instance
        pred (dict): Prediction w/ model_name_or_path, model_patch, instance_id
        run_id (str): Run ID
        timeout (int): Timeout for running tests
    """
    instance_id = test_spec.instance_id
    log_dir = get_log_dir(pred, run_id, instance_id)
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "run_instance.log"

    logger = setup_logger(instance_id, log_file, add_stdout=True)

    try:
        runner = ModalSandboxRuntime(test_spec, timeout)
    except Exception as e:
        print(f"Error creating sandbox: {e}")
        raise EvaluationError(
            instance_id,
            f"Error creating sandbox: {e}",
            logger,
        ) from e

    patch_diff = pred.get("model_patch", "")

    try:
        patch_file = "/tmp/patch.diff"
        runner.write_file(patch_file, patch_diff)

        apply_patch_output, returncode = runner.exec(
            "cd /testbed && git apply -v /tmp/patch.diff",
        )

        if returncode != 0:
            logger.info("Failed to apply patch to container, trying again...")

            apply_patch_output, returncode = runner.exec(
                "cd /testbed && patch --batch --fuzz=5 -p1 -i /tmp/patch.diff",
            )

            if returncode != 0:
                logger.info(f"{APPLY_PATCH_FAIL}:\n{apply_patch_output}")
                raise EvaluationError(
                    instance_id,
                    f"{APPLY_PATCH_FAIL}:\n{apply_patch_output}",
                    logger,
                )
            else:
                logger.info(f"{APPLY_PATCH_PASS}:\n{apply_patch_output}")
        else:
            logger.info(f"{APPLY_PATCH_PASS}:\n{apply_patch_output}")

        # Get git diff before running eval script
        git_diff_output_before, returncode = runner.exec(
            "cd /testbed && git diff",
        )
        logger.info(f"Git diff before:\n{git_diff_output_before}")

        eval_file = "/root/eval.sh"
        eval_script = test_spec.eval_script
        # django hack
        eval_script = eval_script.replace("locale-gen", "locale-gen en_US.UTF-8")
        runner.write_file(eval_file, eval_script)

        start_time = time.time()

        run_command = "cd /testbed"
        # pylint hack
        if "pylint" in test_spec.instance_id:
            run_command += " && PYTHONPATH="
        # increase recursion limit for testing
        run_command += " && python3 -c 'import sys; sys.setrecursionlimit(10000)'"
        # run eval script
        run_command += " && /bin/bash /root/eval.sh"
        test_output, returncode = runner.exec(run_command)

        total_runtime = time.time() - start_time

        test_output_path = log_dir / "test_output.txt"
        logger.info(f"Test runtime: {total_runtime:_.2f} seconds")
        with open(test_output_path, "w") as f:
            f.write(test_output)
            logger.info(f"Test output for {instance_id} written to {test_output_path}")
            print(f"Test output for {instance_id} written to {test_output_path}")

        # Get git diff after running eval script
        git_diff_output_after, returncode = runner.exec("cd /testbed && git diff")

        # Check if git diff changed after running eval script
        logger.info(f"Git diff after:\n{git_diff_output_after}")
        if git_diff_output_after != git_diff_output_before:
            logger.info("Git diff changed after running eval script")

        # Get report from test output
        logger.info(f"Grading answer for {instance_id}...")
        report = get_eval_report(
            test_spec=test_spec,
            prediction=pred,
            test_log_path=test_output_path,
            include_tests_status=True,
        )
        logger.info(
            f"report: {report}\nResult for {instance_id}: resolved: {report[instance_id]['resolved']}"
        )

        return TestOutput(
            instance_id=instance_id,
            test_output=test_output,
            report_json_str=json.dumps(report, indent=4),
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=False,
        )
    except modal_lib.exception.SandboxTimeoutError as e:
        raise EvaluationError(
            instance_id,
            f"Test timed out after {timeout} seconds.",
            logger,
        ) from e
    except EvaluationError:
        error_msg = traceback.format_exc()
        logger.info(error_msg)
        return TestOutput(
            instance_id=instance_id,
            test_output="",
            report_json_str="",
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=True,
        )
    except Exception as e:
        error_msg = f"Error in evaluating model for {instance_id}: {e}\n{traceback.format_exc()}\nCheck ({logger.log_file}) for more information."
        logger.exception(error_msg)
        return TestOutput(
            instance_id=instance_id,
            test_output="",
            report_json_str="",
            run_instance_log=log_file.read_text(),
            patch_diff=patch_diff,
            log_dir=log_dir,
            errored=True,
        )


def patched_swebench_eval(  # Defaults from swebench harness
    predictions_path,  # Required argument
    run_id,  # Required argument
    dataset_name="princeton-nlp/SWE-bench_Lite",
    split="test",
    instance_ids=None,
    max_workers=4,
    open_file_limit=4096,
    timeout=1800,
    force_rebuild=False,
    cache_level="env",
    clean=False,
    namespace="swebench",
    instance_image_tag="latest",
    rewrite_reports=False,
    report_dir=".",
    modal=False,
    **kwargs,
):
    with (
        patch(
            "swebench.harness.modal_eval.run_evaluation_modal.run_instance_modal",
            modal_lib.Function.from_name(
                app_name="swebench-agent-run",
                name="run_instance_modal",
            ),
        ),
        patch(
            "swebench.harness.modal_eval.run_evaluation_modal.app",
            app,
        ),
    ):
        # Don't want swebench to run app.run() again
        app.run = nullcontext
        return main(
            dataset_name=dataset_name,
            split=split,
            instance_ids=instance_ids,
            predictions_path=predictions_path,
            max_workers=max_workers,
            force_rebuild=force_rebuild,
            cache_level=cache_level,
            clean=clean,
            open_file_limit=open_file_limit,
            run_id=run_id,
            timeout=timeout,
            namespace=namespace,
            rewrite_reports=rewrite_reports,
            modal=modal,
            instance_image_tag=instance_image_tag,
            report_dir=report_dir,
            **kwargs,
        )
