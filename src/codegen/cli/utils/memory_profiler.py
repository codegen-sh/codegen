import functools
import json
import os
import subprocess
import sys
import tempfile
import time
import tracemalloc
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

import matplotlib.pyplot as plt
import psutil
from rich.console import Console
from rich.table import Table

console = Console()


@dataclass
class MemorySnapshot:
    """A snapshot of memory usage at a point in time."""

    timestamp: float
    rss_mb: float  # Resident Set Size in MB
    vms_mb: float  # Virtual Memory Size in MB
    tracemalloc_mb: Optional[float] = None  # Tracemalloc total in MB

    def to_dict(self) -> dict:
        return {"timestamp": self.timestamp, "rss_mb": self.rss_mb, "vms_mb": self.vms_mb, "tracemalloc_mb": self.tracemalloc_mb}


class MemoryProfiler:
    """A memory profiler that tracks memory usage over time."""

    def __init__(self, interval: float = 0.1, use_tracemalloc: bool = True):
        """Initialize the memory profiler.

        Args:
            interval: The interval in seconds between memory snapshots.
            use_tracemalloc: Whether to use tracemalloc for detailed memory tracking.
        """
        self.interval = interval
        self.use_tracemalloc = use_tracemalloc
        self.snapshots: list[MemorySnapshot] = []
        self.process = psutil.Process(os.getpid())
        self.start_time = None
        self._running = False

    def start(self):
        """Start memory profiling."""
        if self._running:
            return

        self.snapshots = []
        self.start_time = time.time()

        if self.use_tracemalloc:
            tracemalloc.start()

        self._running = True
        self._take_snapshot()

    def stop(self) -> list[MemorySnapshot]:
        """Stop memory profiling and return the snapshots."""
        if not self._running:
            return self.snapshots

        self._take_snapshot()  # Take one final snapshot

        if self.use_tracemalloc:
            tracemalloc.stop()

        self._running = False
        return self.snapshots

    def _take_snapshot(self):
        """Take a snapshot of the current memory usage."""
        mem_info = self.process.memory_info()

        snapshot = MemorySnapshot(
            timestamp=time.time() - self.start_time,
            rss_mb=mem_info.rss / (1024 * 1024),
            vms_mb=mem_info.vms / (1024 * 1024),
        )

        if self.use_tracemalloc:
            current, peak = tracemalloc.get_traced_memory()
            snapshot.tracemalloc_mb = current / (1024 * 1024)

        self.snapshots.append(snapshot)

    def get_peak_memory(self) -> tuple[float, float]:
        """Get the peak RSS and VMS memory usage in MB."""
        if not self.snapshots:
            return 0.0, 0.0

        peak_rss = max(s.rss_mb for s in self.snapshots)
        peak_vms = max(s.vms_mb for s in self.snapshots)
        return peak_rss, peak_vms

    def get_tracemalloc_stats(self, top_n: int = 10) -> list:
        """Get the top memory allocations from tracemalloc."""
        if not self.use_tracemalloc or not tracemalloc.is_tracing():
            return []

        snapshot = tracemalloc.take_snapshot()
        stats = snapshot.statistics("lineno")
        return stats[:top_n]

    def save_report(self, output_dir: Union[str, Path], command_name: str):
        """Save a memory profiling report to the specified directory."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save raw data as JSON
        data_file = output_dir / f"{command_name}_memory_profile.json"
        with open(data_file, "w") as f:
            json.dump([s.to_dict() for s in self.snapshots], f, indent=2)

        # Generate and save plot
        self._generate_plot(output_dir / f"{command_name}_memory_profile.png")

        # Generate text report with tracemalloc stats if available
        report_file = output_dir / f"{command_name}_memory_report.txt"
        with open(report_file, "w") as f:
            peak_rss, peak_vms = self.get_peak_memory()
            f.write(f"Memory Profile for: {command_name}\n")
            f.write(f"{'=' * 50}\n")
            f.write(f"Duration: {self.snapshots[-1].timestamp:.2f} seconds\n")
            f.write(f"Peak RSS: {peak_rss:.2f} MB\n")
            f.write(f"Peak VMS: {peak_vms:.2f} MB\n\n")

            if self.use_tracemalloc:
                f.write("Top Memory Allocations:\n")
                f.write(f"{'-' * 50}\n")
                for stat in self.get_tracemalloc_stats(top_n=20):
                    f.write(f"{stat.size / (1024 * 1024):.2f} MB: {stat.traceback.format()[0]}\n")

        return output_dir

    def _generate_plot(self, output_file: Path):
        """Generate a plot of memory usage over time."""
        if not self.snapshots:
            return

        timestamps = [s.timestamp for s in self.snapshots]
        rss_values = [s.rss_mb for s in self.snapshots]
        vms_values = [s.vms_mb for s in self.snapshots]

        plt.figure(figsize=(10, 6))
        plt.plot(timestamps, rss_values, label="RSS (MB)", linewidth=2)
        plt.plot(timestamps, vms_values, label="VMS (MB)", linewidth=2)

        if self.use_tracemalloc:
            tracemalloc_values = [s.tracemalloc_mb for s in self.snapshots if s.tracemalloc_mb is not None]
            if tracemalloc_values:
                tracemalloc_timestamps = timestamps[: len(tracemalloc_values)]
                plt.plot(tracemalloc_timestamps, tracemalloc_values, label="Tracemalloc (MB)", linewidth=2, linestyle="--")

        plt.xlabel("Time (seconds)")
        plt.ylabel("Memory Usage (MB)")
        plt.title("Memory Usage Over Time")
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.legend()

        plt.tight_layout()
        plt.savefig(output_file)
        plt.close()


def profile_memory(func=None, *, interval: float = 0.1, use_tracemalloc: bool = True, output_dir: Optional[Union[str, Path]] = None):
    """Decorator to profile memory usage of a function.

    Args:
        func: The function to profile.
        interval: The interval in seconds between memory snapshots.
        use_tracemalloc: Whether to use tracemalloc for detailed memory tracking.
        output_dir: Directory to save the memory profile report. If None, a temporary directory is used.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            profiler = MemoryProfiler(interval=interval, use_tracemalloc=use_tracemalloc)
            profiler.start()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                profiler.stop()

                # Determine output directory
                out_dir = output_dir
                if out_dir is None:
                    out_dir = Path(tempfile.gettempdir()) / "codegen_memory_profiles"

                # Save report
                func_name = func.__name__
                report_dir = profiler.save_report(out_dir, func_name)

                console.print(f"\n[bold green]Memory profile saved to:[/bold green] {report_dir}")

                # Print summary
                peak_rss, peak_vms = profiler.get_peak_memory()
                table = Table(title="Memory Usage Summary")
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="green")

                table.add_row("Peak RSS", f"{peak_rss:.2f} MB")
                table.add_row("Peak VMS", f"{peak_vms:.2f} MB")
                table.add_row("Duration", f"{profiler.snapshots[-1].timestamp:.2f} seconds")

                console.print(table)

        return wrapper

    if func is None:
        return decorator
    return decorator(func)


def profile_command(cmd_args: list[str], output_dir: Optional[Union[str, Path]] = None) -> Path:
    """Profile memory usage of a command.

    Args:
        cmd_args: The command arguments to profile.
        output_dir: Directory to save the memory profile report. If None, a temporary directory is used.

    Returns:
        Path to the output directory containing the profile report.
    """
    if output_dir is None:
        output_dir = Path(tempfile.gettempdir()) / "codegen_memory_profiles"
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create a unique filename for this run
    timestamp = int(time.time())
    cmd_name = "_".join(cmd_args).replace("/", "_")[:50]  # Limit length and remove problematic chars
    output_file = output_dir / f"{cmd_name}_{timestamp}_memory.json"

    # Run the command with memory profiling
    env = os.environ.copy()
    env["PYTHONPATH"] = f"{os.getcwd()}:{env.get('PYTHONPATH', '')}"

    # Prepare the profiling script
    script = f"""
import sys
import time
import json
import psutil
import tracemalloc
from pathlib import Path

output_file = "{output_file}"
interval = 0.1
process = psutil.Process()
snapshots = []
start_time = time.time()

# Start tracemalloc
tracemalloc.start()

# Take snapshots at regular intervals
try:
    while True:
        mem_info = process.memory_info()
        current, peak = tracemalloc.get_traced_memory()

        snapshots.append({{
            "timestamp": time.time() - start_time,
            "rss_mb": mem_info.rss / (1024 * 1024),
            "vms_mb": mem_info.vms / (1024 * 1024),
            "tracemalloc_mb": current / (1024 * 1024)
        }})

        time.sleep(interval)
except KeyboardInterrupt:
    pass
finally:
    # Save the snapshots
    with open(output_file, 'w') as f:
        json.dump(snapshots, f, indent=2)

    # Print summary
    if snapshots:
        peak_rss = max(s["rss_mb"] for s in snapshots)
        peak_vms = max(s["vms_mb"] for s in snapshots)
        duration = snapshots[-1]["timestamp"]

        print(f"\\nMemory Profile Summary:")
        print(f"Peak RSS: {{peak_rss:.2f}} MB")
        print(f"Peak VMS: {{peak_vms:.2f}} MB")
        print(f"Duration: {{duration:.2f}} seconds")
        print(f"Profile saved to: {{output_file}}")
    """

    script_file = output_dir / f"memory_profiler_{timestamp}.py"
    with open(script_file, "w") as f:
        f.write(script)

    # Start the profiler in a separate process
    profiler_process = subprocess.Popen([sys.executable, str(script_file)], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Run the command
    cmd_process = subprocess.Popen([sys.executable, "-m", "codegen.cli.cli", *cmd_args], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Wait for the command to finish
    stdout, stderr = cmd_process.communicate()

    # Stop the profiler
    profiler_process.terminate()
    profiler_stdout, profiler_stderr = profiler_process.communicate()

    # Print command output
    console.print("[bold]Command Output:[/bold]")
    console.print(stdout.decode())
    if stderr:
        console.print("[bold red]Command Errors:[/bold red]")
        console.print(stderr.decode())

    # Print profiler output
    if profiler_stdout:
        console.print(profiler_stdout.decode())

    # Generate visualization if the profile data exists
    if output_file.exists():
        try:
            with open(output_file) as f:
                data = json.load(f)

            if data:
                # Generate plot
                plot_file = output_dir / f"{cmd_name}_{timestamp}_memory.png"

                timestamps = [s["timestamp"] for s in data]
                rss_values = [s["rss_mb"] for s in data]
                vms_values = [s["vms_mb"] for s in data]
                tracemalloc_values = [s["tracemalloc_mb"] for s in data if "tracemalloc_mb" in s]

                plt.figure(figsize=(10, 6))
                plt.plot(timestamps, rss_values, label="RSS (MB)", linewidth=2)
                plt.plot(timestamps, vms_values, label="VMS (MB)", linewidth=2)

                if tracemalloc_values:
                    tracemalloc_timestamps = timestamps[: len(tracemalloc_values)]
                    plt.plot(tracemalloc_timestamps, tracemalloc_values, label="Tracemalloc (MB)", linewidth=2, linestyle="--")

                plt.xlabel("Time (seconds)")
                plt.ylabel("Memory Usage (MB)")
                plt.title(f"Memory Usage: {' '.join(cmd_args)}")
                plt.grid(True, linestyle="--", alpha=0.7)
                plt.legend()

                plt.tight_layout()
                plt.savefig(plot_file)
                plt.close()

                console.print(f"[bold green]Memory profile visualization saved to:[/bold green] {plot_file}")
        except Exception as e:
            console.print(f"[bold red]Error generating visualization:[/bold red] {e}")

    return output_dir
