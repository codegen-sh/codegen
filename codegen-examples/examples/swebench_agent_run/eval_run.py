import asyncio
import json
import traceback
from pathlib import Path
import modal
from datetime import datetime
from codegen.extensions.langchain.utils import get_swe_bench_examples
from codegen.extensions.swebench.report import generate_report

PREDS_DNAME = Path(__file__).parent / "predictions"
LOG_DIR = Path(__file__).parent / "logs"

process_entry = modal.Function.lookup("swebench-agent-run", "process_entry")


async def process_batch(examples, batch_size=50):
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
        batch_tasks = [process_entry.remote.aio(example) for example in batch]

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

                    if isinstance(result, modal.exception.ModalClientError):
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


async def run_eval(use_existing_preds=False):
    try:
        if not use_existing_preds:
            # Get all examples
            examples = get_swe_bench_examples()[:1]
            print(f"Processing {len(examples)} examples...")

            # Create output directory if it doesn't exist
            PREDS_DNAME.mkdir(exist_ok=True)
            results_dir = PREDS_DNAME / "results"
            results_dir.mkdir(exist_ok=True)

            # Create a timestamp for this run
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Process all examples in parallel batches
            results = await process_batch(examples)

            # Save individual results
            for result in results:
                if result and "instance_id" in result:
                    instance_id = result["instance_id"]
                    output_file = results_dir / f"{instance_id}.json"
                    with open(output_file, "w") as f:
                        json.dump(result, f, indent=4)

            # Save summary file
            summary_file = results_dir / f"summary_{timestamp}.json"
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
            print(f"Results saved to: {results_dir}")
            print(f"Summary saved to: {summary_file}")
            print(f"Successful: {summary['successful']}/{summary['total_examples']}")
            print(f"Failed: {summary['failed']}/{summary['total_examples']}")
            if summary["error_types"]:
                print("\nError type distribution:")
                for error_type, count in summary["error_types"].items():
                    print(f"  {error_type}: {count}")

        # Generate Report on Modal
        generate_report(PREDS_DNAME, LOG_DIR)
    except Exception:
        print("Fatal error in run_eval:")
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(run_eval())
