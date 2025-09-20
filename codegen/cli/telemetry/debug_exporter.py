"""Debug exporter for OpenTelemetry that writes spans to local files.

This module provides a debug exporter that writes telemetry data to disk
for easy inspection and debugging of CLI telemetry.
"""

import json
import os
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.trace import format_span_id, format_trace_id

from codegen.configs.constants import GLOBAL_CONFIG_DIR


class DebugFileSpanExporter(SpanExporter):
    """Exports spans to JSON files for debugging."""

    def __init__(self, output_dir: Path | None = None):
        """Initialize the debug exporter.

        Args:
            output_dir: Directory to write debug files. Defaults to ~/.config/codegen-sh/telemetry_debug
        """
        if output_dir is None:
            output_dir = GLOBAL_CONFIG_DIR / "telemetry_debug"

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create a session file for this CLI run
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_file = self.output_dir / f"session_{self.session_id}.jsonl"

        # Write session header
        with open(self.session_file, "w") as f:
            f.write(
                json.dumps(
                    {
                        "type": "session_start",
                        "timestamp": datetime.now().isoformat(),
                        "pid": os.getpid(),
                    }
                )
                + "\n"
            )

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to file.

        Args:
            spans: Spans to export

        Returns:
            Export result status
        """
        try:
            with open(self.session_file, "a") as f:
                for span in spans:
                    # Convert span to JSON-serializable format
                    span_data = {
                        "type": "span",
                        "name": span.name,
                        "trace_id": format_trace_id(span.context.trace_id),
                        "span_id": format_span_id(span.context.span_id),
                        "parent_span_id": format_span_id(span.parent.span_id) if span.parent else None,
                        "start_time": span.start_time,
                        "end_time": span.end_time,
                        "duration_ms": (span.end_time - span.start_time) / 1_000_000 if span.end_time else None,
                        "status": {
                            "status_code": span.status.status_code.name,
                            "description": span.status.description,
                        },
                        "attributes": dict(span.attributes or {}),
                        "events": [
                            {
                                "name": event.name,
                                "timestamp": event.timestamp,
                                "attributes": dict(event.attributes or {}),
                            }
                            for event in span.events
                        ],
                        "resource": dict(span.resource.attributes),
                    }

                    # Handle exceptions
                    if span.status.status_code.name == "ERROR" and span.events:
                        for event in span.events:
                            if event.name == "exception":
                                span_data["exception"] = dict(event.attributes or {})

                    f.write(json.dumps(span_data, default=str) + "\n")

            return SpanExportResult.SUCCESS

        except Exception as e:
            print(f"[Telemetry Debug] Failed to write spans: {e}")
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        # Write session end marker
        try:
            with open(self.session_file, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "type": "session_end",
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass


class DebugConsoleSpanExporter(SpanExporter):
    """Exports spans to console for debugging."""

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Export spans to console.

        Args:
            spans: Spans to export

        Returns:
            Export result status
        """
        try:
            for span in spans:
                duration_ms = (span.end_time - span.start_time) / 1_000_000 if span.end_time else 0

                print(f"\n[Telemetry] {span.name}")
                print(f"  Duration: {duration_ms:.2f}ms")
                print(f"  Status: {span.status.status_code.name}")

                if span.attributes:
                    print("  Attributes:")
                    for key, value in span.attributes.items():
                        print(f"    {key}: {value}")

                if span.events:
                    print("  Events:")
                    for event in span.events:
                        print(f"    - {event.name}")
                        if event.attributes:
                            for key, value in event.attributes.items():
                                print(f"      {key}: {value}")

                if span.status.description:
                    print(f"  Error: {span.status.description}")

            return SpanExportResult.SUCCESS

        except Exception as e:
            print(f"[Telemetry Debug] Console export failed: {e}")
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        """Shutdown the exporter."""
        pass
