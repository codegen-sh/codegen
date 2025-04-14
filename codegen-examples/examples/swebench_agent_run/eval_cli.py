import json
import traceback
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple

import click
import modal
from codegen.extensions.swebench.harness import run_agent_on_entry
from codegen.extensions.swebench.utils import (
    SWEBenchDataset,
    SweBenchExample,
    get_swe_bench_examples,
)
from codegen.sdk.core.codebase import Codebase

from swebench_agent_run.constants import DATASET_DICT
from swebench_agent_run.report import generate_report
from swebench_agent_run.utils import track_batches

# Constants
PREDS_DNAME = Path(__file__).parent / "predictions"
LOG_DIR = Path(__file__).parent / "logs"

# Modal function setup
run_agent_modal = modal.Function.from_name(
    app_name="swebench-agent-run",
    name="run_agent_modal",
)


# Type aliases
@dataclass
class ErrorInfo:
    error_type: str
    error_message: str
    traceback: str
    modal_error_code: Optional[str] = None
    modal_error_details: Optional[dict] = None

    def format_error(self, example_id: str = "") -> Dict[str, Any]:
        """Format error information into a structured dictionary."""
        error_dict = {
            "error_context": "Processing error"
            if not example_id
            else f"Error processing {example_id}",
            "error_details": {
                "type": self.error_type,
                "message": self.error_message,
                "traceback": self.traceback.split("\n"),  # Split for better JSON formatting
            },
        }

        if self.modal_error_code or self.modal_error_details:
            error_dict["error_details"]["modal_specific"] = {
                "error_code": self.modal_error_code,
                "error_details": self.modal_error_details,
            }

        return error_dict


@dataclass
class ProcessingResult:
    instance_id: str
    status: Optional[str] = None
    error_info: Optional[ErrorInfo] = None
    result: Optional[dict] = None

    ERROR_STATUS: ClassVar[str] = "error"  # Class constant for error status

    @classmethod
    def create_error(cls, instance_id: str, error_info: ErrorInfo) -> "ProcessingResult":
        """Create a ProcessingResult instance for an error case."""
        return cls(instance_id=instance_id, status=cls.ERROR_STATUS, error_info=error_info)


def create_error_info(error: Exception, example_id: str = "") -> ErrorInfo:
    """Create standardized error information."""
    traceback_str = (
        "".join(traceback.format_exception(type(error), error, error.__traceback__))
        if hasattr(error, "__traceback__")
        else traceback.format_exc()
    )

    error_info = ErrorInfo(
        error_type=type(error).__name__,
        error_message=str(error),
        traceback=traceback_str,
    )

    if isinstance(error, modal.exception.Error):
        error_info.modal_error_code = getattr(error, "code", None)
        error_info.modal_error_details = getattr(error, "details", None)

    # Print formatted error as JSON
    print(json.dumps(error_info.format_error(example_id), indent=2))

    return error_info


def process_modal(
    examples: list[SweBenchExample],
    model: str,
    run_id: str,
) -> List[ProcessingResult]:
    """Process examples using Modal's parallel execution."""
    results: List[ProcessingResult] = []

    try:
        batch_results = run_agent_modal.starmap(
            [(ex, run_id, model) for ex in examples],
        )

        for example, result in zip(examples, batch_results):
            if isinstance(result, Exception):
                error_info = create_error_info(result, example.instance_id)
                results.append(ProcessingResult.create_error(example.instance_id, error_info))
            elif result is None:
                print(f"Warning: Null result for {example.instance_id}")
                results.append(
                    ProcessingResult.create_error(
                        example.instance_id,
                        ErrorInfo(
                            error_type="NullResult",
                            error_message="Process returned None",
                        ),
                    )
                )
            else:
                results.append(ProcessingResult(instance_id=example.instance_id, result=result))

    except Exception as e:
        error_info = create_error_info(e)
        # Mark all examples as failed
        results.extend(
            [ProcessingResult.create_error(example.instance_id, error_info) for example in examples]
        )

    return results


def process_batch_local(
    examples: list[SweBenchExample],
    batch_size: int = 10,
    codebases: dict[str, Codebase] = {},
    model: str = "claude-3-7-sonnet-latest",
    run_id: str | None = None,
) -> List[ProcessingResult]:
    """Process examples in local batches."""
    results: List[ProcessingResult] = []

    for _, batch in track_batches(examples, batch_size, desc="Processing examples"):
        for example in batch:
            try:
                result = run_agent_on_entry(
                    example,
                    model=model,
                    codebase=codebases.get(example.instance_id),
                    run_id=run_id,
                )
                results.append(ProcessingResult(instance_id=example.instance_id, result=result))
            except Exception as e:
                error_info = create_error_info(e, example.instance_id)
                results.append(ProcessingResult.create_error(example.instance_id, error_info))

    return results


def save_results(
    results: List[ProcessingResult], predictions_dir: Path, timestamp: str
) -> Tuple[Path, dict]:
    """Save individual results and create summary."""
    # Save individual results
    for result in results:
        output_file = predictions_dir / f"{result.instance_id}.json"
        output_file.parent.mkdir(exist_ok=True, parents=True)
        with open(output_file, "w") as f:
            # Convert dataclass to dict for JSON serialization
            json.dump(asdict(result), f, indent=4)

    # Create and save summary
    summary = {
        "timestamp": timestamp,
        "total_examples": len(results),
        "successful": len([r for r in results if not r.status]),  # No status means success
        "failed": len([r for r in results if r.status == ProcessingResult.ERROR_STATUS]),
        "error_types": {},
        "results": [asdict(r) for r in results],  # Convert all results to dict
    }

    # Collect error statistics
    for result in results:
        if result.status == ProcessingResult.ERROR_STATUS and result.error_info:
            error_type = result.error_info.error_type
            summary["error_types"][error_type] = summary["error_types"].get(error_type, 0) + 1

    summary_file = predictions_dir / f"summary_{timestamp}.json"
    with open(summary_file, "w") as f:
        json.dump(summary, f, indent=4)

    return summary_file, summary


def print_summary(summary: dict, predictions_dir: Path, summary_file: Path) -> None:
    """Print processing summary information."""
    print("\nProcessing complete!")
    print(f"Results saved to: {predictions_dir}")
    print(f"Summary saved to: {summary_file}")
    print(f"Successful: {summary['successful']}/{summary['total_examples']}")
    print(f"Failed: {summary['failed']}/{summary['total_examples']}")

    if summary["error_types"]:
        print("\nError type distribution:")
        for error_type, count in summary["error_types"].items():
            print(f"  {error_type}: {count}")


def run_eval(
    use_existing_preds: Optional[str],
    dataset_enum: SWEBenchDataset,
    length: int,
    instance_id: Optional[str] = None,
    local: bool = False,
    codebases: Dict[str, Codebase] = {},
    repo: Optional[str] = None,
    model: str = "claude-3-7-sonnet-latest",
    instance_ids: list[str] | None = None,
) -> Tuple[Path, Path, SWEBenchDataset, str]:
    """Main evaluation function."""
    run_id = use_existing_preds or str(uuid.uuid4())
    print(f"Run ID: {run_id}")

    predictions_dir = PREDS_DNAME / f"results_{run_id}"

    examples = get_swe_bench_examples(
        dataset=dataset_enum,
        length=length,
        instance_id=instance_id,
        repo=repo,
        instance_ids=instance_ids or [],
    )
    print(
        "Examples:\n" + "\n".join(f"{e.instance_id} - {e.repo} - {e.base_commit}" for e in examples)
    )

    try:
        if use_existing_preds is None:
            print(f"Repo: {repo}")
            print(
                f"Examples:\n{'\n'.join([f'{e.instance_id} - {e.repo} - {e.base_commit}' for e in examples])}"
            )
            print(f"Processing {len(examples)} examples...")

            predictions_dir.mkdir(exist_ok=True, parents=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            results = (
                process_batch_local(
                    examples,
                    codebases=codebases,
                    model=model,
                    run_id=run_id,
                )
                if local
                else process_modal(examples, model=model, run_id=run_id)
            )
            summary_file, summary = save_results(results, predictions_dir, timestamp)
            print_summary(summary, predictions_dir, summary_file)

        return predictions_dir, LOG_DIR, dataset_enum, run_id
    except Exception:
        traceback.print_exc()
        raise


def list_of_strings(value: str) -> list[str]:
    if value == "":
        return []
    return value.split(",")


@click.command()
@click.option(
    "--use-existing-preds",
    help="The run ID of the existing predictions to use.",
    type=str,
    default=None,
)
@click.option(
    "--dataset",
    help="The dataset to use.",
    type=click.Choice(["lite", "full", "verified"]),
    default="lite",
)
@click.option("--length", help="The number of examples to process.", type=int, default=10)
@click.option(
    "--instance-id",
    help="The instance ID of the example to process.",
    type=str,
    default=None,
)
@click.option("--local", help="Run the evaluation locally.", is_flag=True, default=False)
@click.option("--push-metrics", help="Push metrics to the database.", is_flag=True, default=False)
@click.option("--repo", help="The repo to use.", type=str, default=None)
@click.option("--model", help="The model to use.", type=str, default="claude-3-7-sonnet-latest")
@click.option(
    "--instance-ids",
    help="The instance IDs of the examples to process. Example: --instance-ids <instance_id1>,<instance_id2>,...",
    type=list_of_strings,
    default="",
)
def main(
    use_existing_preds: Optional[str],
    dataset: str,
    length: int,
    instance_id: Optional[str],
    local: bool,
    repo: Optional[str],
    model: str,
    push_metrics: bool,
    instance_ids: list[str],
) -> None:
    """Command-line interface for running evaluations."""
    print(f"Repo: {repo}")
    result = run_eval(
        use_existing_preds=use_existing_preds,
        dataset_enum=DATASET_DICT[dataset],
        length=length,
        instance_id=instance_id,
        local=local,
        repo=repo,
        model=model,
        instance_ids=instance_ids,
    )

    generate_report(*result)

    evaluation_result_file = Path(f"results.{result[3]}.json")

    if push_metrics:
        if not evaluation_result_file.exists() and use_existing_preds is None:
            print("Evaluation was not run - no metrics were pushed")
            return

        try:
            from swebench_agent_run.metrics import (
                write_report_to_db,  # delay import because of extras
            )

            write_report_to_db(str(evaluation_result_file.resolve()))
        except Exception:
            print("Error writing report to db")
            traceback.print_exc()


if __name__ == "__main__":
    main()
