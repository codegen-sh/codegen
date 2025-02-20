import csv
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

import psutil

from codegen_on_oss.errors import ParseRunError

if TYPE_CHECKING:
    # Logger only available in type checking context.
    from loguru import Logger  # type: ignore[attr-defined]


class MetricsProfiler:
    """
    A helper to record performance metrics across multiple profiles and write them to a CSV.

    Usage:

        metrics_profiler = MetricsProfiler(output_path="metrics.csv")

        with metrics_profiler.start_profiler(name="profile_1") as profile:
            # Some code block...
            profile.measure("step 1")
            # More code...
            profile.measure("step 2")

        # The CSV "metrics.csv" now contains the measurements for profile_1.
    """

    def __init__(self, output_path: str):
        self.output_path = output_path

    @contextmanager
    def start_profiler(self, name: str, revision: str, logger: "Logger"):
        """
        Starts a new profiling session for a given profile name.
        Returns a MetricsProfile instance that you can use to mark measurements.
        """
        profile = MetricsProfile(name, revision, self.output_path, logger)
        error_msg: str | None = None
        try:
            yield profile
        except ParseRunError as e:
            logger.error(f"Repository: {name} {e.args[0]}")  # noqa: TRY400
            error_msg = e.args[0]
        except Exception as e:
            logger.exception(f"Repository: {name}")
            error_msg = f"Unhandled Exception {type(e)}"

        finally:
            profile.finish(error=error_msg)


class MetricsProfile:
    """
    Context-managed profile that records measurements at each call to `measure()`.
    It tracks the wall-clock duration, CPU time, and memory usage (with delta) at the time of the call.
    Upon exiting the context, it also writes all collected metrics, including the total time,
    to a CSV file.
    """

    if TYPE_CHECKING:
        logger: "Logger"
        measurements: list[dict[str, Any]]

    def __init__(
        self, name: str, revision: str, output_path: str | None, logger: "Logger"
    ):
        self.name = name
        self.revision = revision
        self.output_path = output_path
        self.logger = logger

        # Capture initial metrics.
        self.start_time = time.perf_counter()
        self.start_cpu = time.process_time()
        self.start_mem = psutil.Process(os.getpid()).memory_info().rss

        # For delta calculations, store the last measurement values.
        self.last_measure_time = self.start_time
        self.last_measure_mem = self.start_mem

    def measure(self, step_name: str):
        """
        Records a measurement for the given step. The measurement includes:
          - Delta wall-clock time since the last measurement or the start,
          - Cumulative wall-clock time since the start,
          - The current CPU usage of the process (using time.process_time()),
          - The current memory usage (RSS in bytes),
          - The memory delta (difference from the previous measurement).
        """
        current_time = time.perf_counter()
        current_cpu = time.process_time()
        current_mem = psutil.Process(os.getpid()).memory_info().rss

        # Calculate time deltas.
        delta_time = current_time - self.last_measure_time
        cumulative_time = current_time - self.start_time

        # Calculate memory delta.
        memory_delta = current_mem - self.last_measure_mem

        # Record the measurement.
        measurement = {
            "profile_name": self.name,
            "revision": self.revision,
            "step": step_name,
            "delta_time": delta_time,
            "cumulative_time": cumulative_time,
            "cpu_time": current_cpu,  # CPU usage at this point.
            "memory_usage": current_mem,
            "memory_delta": memory_delta,
            "error": None,
        }
        self._write_csv(measurement)

        # Update last measurement time and memory for the next delta.
        self.last_measure_time = current_time
        self.last_measure_mem = current_mem

    def finish(self, error: str | None = None):
        """
        Called automatically when the profiling context is exited.
        This method records a final measurement (for the total duration) and
        writes all collected metrics to the CSV file.
        """
        finish_time = time.perf_counter()
        finish_cpu = time.process_time()
        finish_mem = psutil.Process(os.getpid()).memory_info().rss

        total_duration = finish_time - self.start_time

        # Calculate final memory delta.
        memory_delta = finish_mem - self.last_measure_mem

        # Record the overall profile measurement.
        summary = {
            "profile_name": self.name,
            "revision": self.revision,
            "step": "TOTAL",
            "delta_time": total_duration,
            "cumulative_time": total_duration,
            "cpu_time": finish_cpu,
            "memory_usage": finish_mem,
            "memory_delta": memory_delta,
            "error": error,
        }

        self._write_csv(summary)

    def _write_csv(self, measurement: dict[str, Any]):
        """
        Writes all measurements to the CSV file specified by output_path.
        If the file does not exist, it creates it and writes headers; otherwise, it appends.
        """
        self.logger.info(json.dumps(measurement, indent=4))

        if self.output_path is None:
            return

        file_exists = os.path.isfile(self.output_path)
        if not file_exists:
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, mode="a", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=measurement.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(measurement)
