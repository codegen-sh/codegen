import asyncio
import json
import traceback
from pathlib import Path
import uuid
import modal
import click
import time
from codegen.extensions.swebench.harness import run_agent_on_entry
from codegen.extensions.swebench.utils import SWEBenchDataset, SweBenchExample, get_swe_bench_examples
from codegen.extensions.swebench.report import generate_report
from codegen.sdk.core.codebase import Codebase

PREDS_DNAME = Path(__file__).parent / "predictions"
LOG_DIR = Path(__file__).parent / "logs"

run_agent_modal = modal.Function.from_name(app_name="swebench-agent-run", name="run_agent_modal")


async def process_batch_modal(examples: list[SweBenchExample], run_id: str, num_workers=5, min_workers=1, max_retries=3):
    """Process a batch of examples concurrently using a queue system with incremental worker scaling.

    Args:
        examples: List of SweBenchExample objects to process
        num_workers: Initial number of examples to process concurrently
        min_workers: Minimum number of concurrent workers to maintain
        max_retries: Maximum number of retries for failed requests
    """
    results = {}
    queue = asyncio.Queue()

    # Shared state for worker management
    state = {
        "active_workers": num_workers,
        "success_streak": 0,
        "last_scaling_time": time.time(),
        "scaling_cooldown": 0,  # seconds between scaling operations
        "worker_tasks": [],
        "running": True,
    }

    # Use a lock to protect shared state during adjustments
    state_lock = asyncio.Lock()

    # Initialize the queue with (example, attempt) tuples
    for example in examples:
        await queue.put((example, 0))  # 0 represents first attempt

    async def scale_down_worker(task_to_cancel=None):
        """Remove a single worker when rate limiting is detected"""
        async with state_lock:
            # Only scale if cooldown period has passed and we're above min_workers
            current_time = time.time()
            if current_time - state["last_scaling_time"] < state["scaling_cooldown"] or state["active_workers"] <= min_workers:
                return False

            # Reset success streak when scaling down
            state["success_streak"] = 0
            state["last_scaling_time"] = current_time

            # If a specific task was provided, cancel it
            if task_to_cancel and task_to_cancel in state["worker_tasks"]:
                print(f"Rate limiting detected! Removing 1 worker, going from {state['active_workers']} to {state['active_workers'] - 1}")
                state["worker_tasks"].remove(task_to_cancel)
                task_to_cancel.cancel()
                state["active_workers"] -= 1
                return True

            # Otherwise, cancel the most recently added worker
            elif state["worker_tasks"]:
                print(f"Rate limiting detected! Removing 1 worker, going from {state['active_workers']} to {state['active_workers'] - 1}")
                task = state["worker_tasks"].pop()
                task.cancel()
                state["active_workers"] -= 1
                return True

            return False

    async def scale_up_worker():
        """Add a single worker when operations have been consistently successful"""
        async with state_lock:
            # Only scale if cooldown period has passed and we're below num_workers
            current_time = time.time()
            if current_time - state["last_scaling_time"] < state["scaling_cooldown"] or state["active_workers"] >= num_workers:
                return False

            # Add a worker after a streak of successful operations
            if state["success_streak"] >= 5:
                print(f"Operations succeeding! Adding 1 worker, going from {state['active_workers']} to {state['active_workers'] + 1}")

                # Create new worker
                if state["running"]:
                    new_task = asyncio.create_task(worker())
                    state["worker_tasks"].append(new_task)
                    state["active_workers"] += 1
                    state["success_streak"] = 0
                    state["last_scaling_time"] = current_time
                    return True

            return False

    async def is_rate_limit_error(error):
        """Determine if an error is due to rate limiting"""
        # Check for common rate limit error patterns
        if isinstance(error, modal.exception.Error):
            error_msg = str(error).lower()
            rate_limit_indicators = ["rate limit", "too many requests", "429", "throttle", "quota exceeded", "capacity", "limit exceeded"]
            return any(indicator in error_msg for indicator in rate_limit_indicators)
        return False

    async def process_example(example, attempt, current_task):
        try:
            result = await run_agent_modal.remote.aio(example, run_id=run_id)

            if result is None:
                print(f"Warning: Null result for {example.instance_id}")
                return {"status": "error", "instance_id": example.instance_id, "error_info": {"error_type": "NullResult", "error_message": "Process returned None"}}

            # Increment success streak and potentially scale up
            async with state_lock:
                state["success_streak"] += 1

            if state["success_streak"] % 5 == 0:  # Check after every 5 successes
                await scale_up_worker()

            return result

        except Exception as e:
            error_type = type(e).__name__
            error_info = {
                "error_type": error_type,
                "error_message": str(e),
                "traceback": traceback.format_exception(type(e), e, e.__traceback__),
            }

            if isinstance(e, modal.exception.Error):
                error_info["modal_error_code"] = getattr(e, "code", None)
                error_info["modal_error_details"] = getattr(e, "details", None)

            print(f"Error processing {example.instance_id} (attempt {attempt + 1}):")
            print(f"Type: {error_type}")
            print(f"Message: {str(e)}")

            # Check if this is a rate limit error
            if await is_rate_limit_error(e):
                print(f"Rate limit detected on task for {example.instance_id}")

                # Scale down by removing this specific worker
                scaled_down = await scale_down_worker(current_task)

                # If we're removing this worker, we need to requeue the task for another worker
                if scaled_down:
                    # Requeue this example with the same attempt count (not incrementing)
                    await queue.put((example, attempt))
                    return None

                # Otherwise add a small delay before retrying
                await asyncio.sleep(2 * (attempt + 1))  # Exponential backoff

            if attempt < max_retries:
                await queue.put((example, attempt + 1))
                return None

            return {"status": "error", "instance_id": example.instance_id, "error_info": error_info}

    async def worker():
        # Store this task reference to allow targeted cancellation
        current_task = asyncio.current_task()

        while state["running"]:
            try:
                # Use a timeout to allow worker to check if it should exit
                try:
                    example, attempt = await asyncio.wait_for(queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                if example.instance_id in results:
                    queue.task_done()
                    continue
                print(f"Processing example {example.instance_id}")
                process_result = await process_example(example, attempt, current_task)

                # If we're still processing this task (not requeued due to rate limiting)
                if process_result is not None:
                    results[example.instance_id] = {"instance_id": example.instance_id, **process_result}
                    print(f"Processed example {example.instance_id}")
                    queue.task_done()

                # If None is returned, the task was requeued due to rate limiting
                # and this worker is being shut down, so exit the loop
                else:
                    print(f"Task for {example.instance_id} has been requeued")
                    queue.task_done()
                    if current_task not in state["worker_tasks"]:
                        break

            except asyncio.CancelledError:
                # Handle graceful cancellation
                print("Worker task cancelled")
                break
            except Exception as e:
                print(f"Worker error: {str(e)}")
                traceback.print_exc()
                queue.task_done()

    # Start initial workers
    state["worker_tasks"] = [asyncio.create_task(worker()) for _ in range(num_workers)]

    # Wait for queue to be fully processed
    await queue.join()

    # Mark as not running and cancel remaining workers
    state["running"] = False
    for w in state["worker_tasks"]:
        w.cancel()

    # Wait for all workers to be cancelled
    await asyncio.gather(*state["worker_tasks"], return_exceptions=True)

    # Return results in the same order as input examples
    return [results.get(example.instance_id, {"instance_id": example.instance_id, "status": "missing"}) for example in examples]


def process_batch_local(examples: list[SweBenchExample], num_workers=5, codebases: dict[str, Codebase] = {}, run_id: str | None = None):
    """Process a batch of examples synchronously.

    Args:
        examples: List of SweBenchExample objects to process
        num_workers: Number of examples to process in each batch.
                   Default is 10 to avoid overwhelming the system.
    """
    results = []

    # Process examples in batches
    for i in range(0, len(examples), num_workers):
        batch = examples[i : i + num_workers]
        print(f"Processing batch {i // num_workers + 1}/{len(examples) // num_workers + 1} (examples {i + 1}-{min(i + num_workers, len(examples))})")

        # Process each example in the batch
        for example in batch:
            try:
                # Run the agent locally instead of using modal
                if codebases and example.instance_id in codebases:
                    result = run_agent_on_entry(example, codebase=codebases[example.instance_id], run_id=run_id)
                else:
                    result = run_agent_on_entry(example, run_id=run_id)
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


async def run_eval(
    use_existing_preds: str | None, dataset: str, length: int, instance_id: str | None = None, local: bool = False, codebases: dict[str, Codebase] = {}, repo: str | None = None, num_workers: int = 5
):
    run_id = use_existing_preds or str(uuid.uuid4())
    print(f"Run ID: {run_id}")
    predictions_dir = PREDS_DNAME / f"results_{run_id}"
    dataset_dict = {
        "lite": SWEBenchDataset.LITE,
        "full": SWEBenchDataset.FULL,
        "verified": SWEBenchDataset.VERIFIED,
    }
    dataset_enum = dataset_dict[dataset]

    examples = get_swe_bench_examples(dataset=dataset_enum, length=length, instance_id=instance_id, repo=repo)

    try:
        if use_existing_preds is None:
            print(f"Repo: {repo}")
            print(f"Examples:\n{'\n'.join([f'{e.instance_id} - {e.repo} - {e.base_commit}' for e in examples])}")
            print(f"Processing {len(examples)} examples...")
            # Create output directory if it doesn't exist
            predictions_dir.mkdir(exist_ok=True, parents=True)

            # Create a timestamp for this run
            timestamp = time.strftime("%Y-%m-%d %H:%M %Z", time.localtime(time.time()))

            # Process all examples in parallel batches
            if local:
                results = process_batch_local(examples, codebases=codebases, run_id=run_id)
            else:
                results = await process_batch_modal(examples, num_workers=num_workers, run_id=run_id)

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
@click.option(
    "--num-workers", help="The number of workers to use. This is the number of examples that will be processed concurrently. A large number may lead to rate limiting issues.", type=int, default=5
)
def run_eval_command(use_existing_preds, dataset, length, instance_id, local, repo, num_workers):
    print(f"Repo: {repo}")
    asyncio.run(run_eval(use_existing_preds=use_existing_preds, dataset=dataset, length=length, instance_id=instance_id, codebases=None, local=local, repo=repo, num_workers=num_workers))


if __name__ == "__main__":
    run_eval_command()
