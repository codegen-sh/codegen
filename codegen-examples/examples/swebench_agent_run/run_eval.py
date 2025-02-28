import asyncio
import json
import traceback
from pathlib import Path
import uuid
import modal
import click
from datetime import datetime
from codegen.extensions.swebench.harness import run_agent_on_entry
from codegen.extensions.swebench.utils import SWEBenchDataset, SweBenchExample, get_swe_bench_examples
from codegen.extensions.swebench.report import generate_report
from codegen.sdk.core.codebase import Codebase

PREDS_DNAME = Path(__file__).parent / "predictions"
LOG_DIR = Path(__file__).parent / "logs"

run_agent_modal = modal.Function.from_name(app_name="swebench-agent-run", name="run_agent_modal")


async def process_batch(examples: list[SweBenchExample], batch_size=10):
    """Process a batch of examples concurrently.

    Args:
        examples: List of SweBenchExample objects to process
        batch_size: Number of examples to process concurrently.
                   Default is 50 which provides good parallelization
                   while staying well within Modal's limits.
    """
    results = []

    # Process examples in batches
    for i in range(0, len(examples), batch_size):
        batch = examples[i : i + batch_size]

        # Create tasks for this batch
        batch_tasks = [run_agent_modal.remote.aio(example) for example in batch]

        # Wait for all tasks in this batch to complete
        print(f"Processing batch {i // batch_size + 1}/{len(examples) // batch_size + 1} (examples {i + 1}-{min(i + batch_size, len(examples))})")

        try:
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)

            # Store results
            for example, result in zip(batch, batch_results):
                error_info = None

                if isinstance(result, Exception):
                    error_type = type(result).__name__
                    error_info = {
                        "error_type": error_type,
                        "error_message": str(result),
                        "traceback": traceback.format_exception(type(result), result, result.__traceback__),
                    }

                    if isinstance(result, modal.exception.Error):
                        error_info["modal_error_code"] = getattr(result, "code", None)
                        error_info["modal_error_details"] = getattr(result, "details", None)

                    print(f"Error processing {example.instance_id}:")
                    print(f"Type: {error_type}")
                    print(f"Message: {str(result)}")
                    print("Traceback:")
                    print("".join(error_info["traceback"]))

                    results.append({"instance_id": example.instance_id, "status": "error", "error_info": error_info})
                else:
                    if result is None:
                        print(f"Warning: Null result for {example.instance_id}")
                        results.append({"instance_id": example.instance_id, "status": "error", "error_info": {"error_type": "NullResult", "error_message": "Process returned None"}})
                    else:
                        results.append(result)

        except Exception as e:
            print("Batch processing error:")
            print(f"Type: {type(e).__name__}")
            print(f"Message: {str(e)}")
            traceback.print_exc()

            # Mark all examples in the batch as failed
            for example in batch:
                results.append(
                    {
                        "instance_id": example.instance_id,
                        "status": "error",
                        "error_info": {"error_type": type(e).__name__, "error_message": str(e), "traceback": traceback.format_exc(), "batch_failure": True},
                    }
                )

    return results


def process_batch_sync(examples: list[SweBenchExample], batch_size=10, codebases: dict[str, Codebase] = {}):
    """Process a batch of examples synchronously.

    Args:
        examples: List of SweBenchExample objects to process
        batch_size: Number of examples to process in each batch.
                   Default is 10 to avoid overwhelming the system.
    """
    results = []

    # Process examples in batches
    for i in range(0, len(examples), batch_size):
        batch = examples[i : i + batch_size]
        print(f"Processing batch {i // batch_size + 1}/{len(examples) // batch_size + 1} (examples {i + 1}-{min(i + batch_size, len(examples))})")

        # Process each example in the batch
        for example in batch:
            try:
                # Run the agent locally instead of using modal
                if codebases and example.instance_id in codebases:
                    result = run_agent_on_entry(example, codebase=codebases[example.instance_id])
                else:
                    result = run_agent_on_entry(example)
                results.append(result)

            except Exception as e:
                error_type = type(e).__name__
                error_info = {
                    "error_type": error_type,
                    "error_message": str(e),
                    "traceback": traceback.format_exc(),
                }

                print(f"Error processing {example.instance_id}:")
                print(f"Type: {error_type}")
                print(f"Message: {str(e)}")
                print("Traceback:")
                print(error_info["traceback"])

                results.append({"instance_id": example.instance_id, "status": "error", "error_info": error_info})

    return results


async def run_eval(use_existing_preds: str | None, dataset: str, length: int, instance_id: str | None = None, local: bool = False, codebases: dict[str, Codebase] = {}, repo: str | None = None):
    run_id = use_existing_preds or str(uuid.uuid4())
    print(f"Run ID: {run_id}")
    predictions_dir = PREDS_DNAME / f"results_{run_id}"
    dataset_dict = {
        "lite": SWEBenchDataset.LITE,
        "full": SWEBenchDataset.FULL,
        "verified": SWEBenchDataset.VERIFIED,
    }
    dataset_enum = dataset_dict[dataset]
    print(repo)
    examples = get_swe_bench_examples(dataset=dataset_enum, length=length, instance_id=instance_id, repo=repo)
    print(f"Examples:\n{'\n'.join([f'{e.instance_id} - {e.repo} - {e.base_commit}' for e in examples])}")

    try:
        if use_existing_preds is None:
            print(f"Processing {len(examples)} examples...")

            # Create output directory if it doesn't exist
            predictions_dir.mkdir(exist_ok=True, parents=True)

            # Create a timestamp for this run
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Process all examples in parallel batches
            if local:
                results = process_batch_sync(examples, codebases=codebases)
            else:
                results = await process_batch(examples)

            # Save individual results
            for result in results:
                if result and "instance_id" in result:
                    instance_id = result["instance_id"]
                    output_file = predictions_dir / f"{instance_id}.json"
                    output_file.parent.mkdir(exist_ok=True, parents=True)
                    with open(output_file, "w") as f:
                        json.dump(result, f, indent=4)

            # Save summary file
            summary_file = predictions_dir / f"summary_{timestamp}.json"
            summary = {
                "timestamp": timestamp,
                "total_examples": len(examples),
                "successful": len([r for r in results if r and "status" not in r]),
                "failed": len([r for r in results if r and "status" in r and r["status"] == "error"]),
                "error_types": {},
                "results": results,
            }

            # Collect error statistics
            for result in results:
                if result and "status" in result and result["status"] == "error":
                    error_type = result.get("error_info", {}).get("error_type", "Unknown")
                    summary["error_types"][error_type] = summary["error_types"].get(error_type, 0) + 1

            with open(summary_file, "w") as f:
                json.dump(summary, f, indent=4)

            print("\nProcessing complete!")
            print(f"Results saved to: {predictions_dir}")
            print(f"Summary saved to: {summary_file}")
            print(f"Successful: {summary['successful']}/{summary['total_examples']}")
            print(f"Failed: {summary['failed']}/{summary['total_examples']}")
            if summary["error_types"]:
                print("\nError type distribution:")
                for error_type, count in summary["error_types"].items():
                    print(f"  {error_type}: {count}")

        # Generate Report on Modal
        generate_report(predictions_dir, LOG_DIR, dataset_enum, run_id)
    except Exception:
        print("Fatal error in run_eval:")
        traceback.print_exc()
        raise


@click.command()
@click.option("--use-existing-preds", help="The run ID of the existing predictions to use.", type=str, default=None)
@click.option("--dataset", help="The dataset to use.", type=click.Choice(["lite", "full", "verified"]), default="lite")
@click.option("--length", help="The number of examples to process.", type=int, default=10)
@click.option("--instance-id", help="The instance ID of the example to process.", type=str, default=None)
@click.option("--local", help="Run the evaluation locally.", is_flag=True, default=False)
@click.option("--repo", help="The repo to use.", type=str, default=None)
def run_eval_command(use_existing_preds, dataset, length, instance_id, local, repo):
    print(f"Repo: {repo}")
    asyncio.run(run_eval(use_existing_preds=use_existing_preds, dataset=dataset, length=length, instance_id=instance_id, codebases=None, local=local, repo=repo))


if __name__ == "__main__":
    run_eval_command()
