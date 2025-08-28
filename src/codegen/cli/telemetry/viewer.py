"""Simple telemetry log viewer for debugging.

This script provides utilities for analyzing telemetry debug logs.
"""

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.tree import Tree

from codegen.configs.constants import GLOBAL_CONFIG_DIR


def load_session(session_file: Path) -> list[dict[str, Any]]:
    """Load all records from a session file."""
    records = []
    with open(session_file) as f:
        for line in f:
            records.append(json.loads(line))
    return records


def print_span_tree(spans: list[dict[str, Any]], console: Console):
    """Print spans as a tree structure."""
    # Build parent-child relationships
    span_by_id = {span["span_id"]: span for span in spans}
    root_spans = []

    for span in spans:
        if not span.get("parent_span_id") or span["parent_span_id"] not in span_by_id:
            root_spans.append(span)

    # Create tree
    tree = Tree("Telemetry Trace Tree")

    def add_span_to_tree(span: dict[str, Any], parent_node):
        """Recursively add span and its children to tree."""
        duration = span.get("duration_ms", 0)
        status = span["status"]["status_code"]
        status_icon = "✅" if status == "OK" else "❌"

        label = f"{status_icon} {span['name']} ({duration:.2f}ms)"
        node = parent_node.add(label)

        # Add key attributes
        attrs = span.get("attributes", {})
        for key, value in attrs.items():
            if key.startswith("cli.") or key.startswith("event."):
                node.add(f"[dim]{key}: {value}[/dim]")

        # Find children
        for other_span in spans:
            if other_span.get("parent_span_id") == span["span_id"]:
                add_span_to_tree(other_span, node)

    # Add root spans
    for root_span in root_spans:
        add_span_to_tree(root_span, tree)

    console.print(tree)


def analyze_session(session_file: Path):
    """Analyze a telemetry session file."""
    console = Console()

    console.print(f"\n[bold]Analyzing session:[/bold] {session_file.name}\n")

    records = load_session(session_file)
    spans = [r for r in records if r["type"] == "span"]

    if not spans:
        console.print("[yellow]No spans found in session[/yellow]")
        return

    # Basic stats
    total_duration = sum(s.get("duration_ms", 0) for s in spans)
    error_count = sum(1 for s in spans if s["status"]["status_code"] == "ERROR")

    console.print(f"[cyan]Total spans:[/cyan] {len(spans)}")
    console.print(f"[cyan]Total duration:[/cyan] {total_duration:.2f}ms")
    console.print(f"[cyan]Errors:[/cyan] {error_count}")
    console.print()

    # Show errors if any
    if error_count > 0:
        console.print("[bold red]Errors:[/bold red]")
        for span in spans:
            if span["status"]["status_code"] == "ERROR":
                console.print(f"  - {span['name']}: {span['status'].get('description', 'Unknown error')}")
        console.print()

    # Show span tree
    print_span_tree(spans, console)

    # Show slowest operations
    console.print("\n[bold]Slowest Operations:[/bold]")
    sorted_spans = sorted(spans, key=lambda s: s.get("duration_ms", 0), reverse=True)
    for span in sorted_spans[:5]:
        duration = span.get("duration_ms", 0)
        console.print(f"  - {span['name']}: {duration:.2f}ms")


def latest_session() -> Path | None:
    """Get the latest session file."""
    debug_dir = GLOBAL_CONFIG_DIR / "telemetry_debug"
    if not debug_dir.exists():
        return None

    session_files = sorted(debug_dir.glob("session_*.jsonl"), reverse=True)
    return session_files[0] if session_files else None


if __name__ == "__main__":
    # Simple CLI for viewing logs
    import sys

    if len(sys.argv) > 1:
        session_file = Path(sys.argv[1])
    else:
        session_file = latest_session()

    if session_file and session_file.exists():
        analyze_session(session_file)
    else:
        print("No session file found. Run with debug enabled first.")
        print("Usage: python -m codegen.cli.telemetry.viewer [session_file.jsonl]")
