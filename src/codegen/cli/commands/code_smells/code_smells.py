"""CLI command for detecting and refactoring code smells."""

import json
from typing import Optional

import click
from rich.console import Console
from rich.tree import Tree

from codegen.cli.sdk.decorator import command
from codegen.sdk.core.codebase import Codebase
from codegen.sdk.extensions.code_smells.detector import CodeSmellDetector, DetectionConfig
from codegen.sdk.extensions.code_smells.refactorer import CodeSmellRefactorer
from codegen.sdk.extensions.code_smells.smells import (
    CodeSmell,
    CodeSmellCategory,
    CodeSmellSeverity,
)
from codegen.shared.enums.programming_language import ProgrammingLanguage
from codegen.shared.logging.get_logger import get_logger

logger = get_logger(__name__)
console = Console()


@command(help="Detect and refactor code smells in your codebase")
@click.option(
    "--path",
    "-p",
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    default=".",
    help="Path to the codebase to analyze",
)
@click.option(
    "--language",
    "-l",
    type=click.Choice(["python", "typescript", "auto"]),
    default="auto",
    help="Programming language of the codebase",
)
@click.option(
    "--severity",
    "-s",
    type=click.Choice(["low", "medium", "high", "critical", "all"]),
    default="all",
    help="Minimum severity level of code smells to detect",
)
@click.option(
    "--category",
    "-c",
    type=click.Choice(["bloaters", "object_orientation_abusers", "change_preventers", "dispensables", "couplers", "all"]),
    default="all",
    help="Category of code smells to detect",
)
@click.option(
    "--refactor",
    "-r",
    is_flag=True,
    help="Automatically refactor detected code smells when possible",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Path to output JSON report",
)
@click.option(
    "--long-function-lines",
    type=int,
    default=50,
    help="Threshold for long function detection (lines)",
)
@click.option(
    "--long-parameter-list",
    type=int,
    default=5,
    help="Threshold for long parameter list detection",
)
@click.option(
    "--duplicate-code-min-lines",
    type=int,
    default=6,
    help="Minimum lines for duplicate code detection",
)
def code_smells(
    path: str,
    language: str,
    severity: str,
    category: str,
    refactor: bool,
    output: Optional[str],
    long_function_lines: int,
    long_parameter_list: int,
    duplicate_code_min_lines: int,
) -> None:
    """Detect and optionally refactor code smells in a codebase.

    This command analyzes a codebase for common code smells like long functions,
    duplicate code, dead code, etc. It can also automatically refactor some of
    these issues.

    Args:
        path: Path to the codebase to analyze
        language: Programming language of the codebase
        severity: Minimum severity level of code smells to detect
        category: Category of code smells to detect
        refactor: Whether to automatically refactor detected code smells
        output: Path to output JSON report
        long_function_lines: Threshold for long function detection
        long_parameter_list: Threshold for long parameter list detection
        duplicate_code_min_lines: Minimum lines for duplicate code detection
    """
    # Determine the programming language
    prog_language = None
    if language != "auto":
        prog_language = ProgrammingLanguage(language.upper())

    # Initialize the codebase
    console.print(f"[bold blue]Analyzing codebase at [cyan]{path}[/cyan]...[/bold blue]")
    codebase = Codebase(path, language=prog_language)

    # Configure the detector
    config = DetectionConfig(
        long_function_lines=long_function_lines,
        long_parameter_list_threshold=long_parameter_list,
        duplicate_code_min_lines=duplicate_code_min_lines,
    )

    # Initialize the detector and refactorer
    detector = CodeSmellDetector(codebase, config)
    refactorer = CodeSmellRefactorer(codebase)

    # Detect code smells
    console.print("[bold blue]Detecting code smells...[/bold blue]")
    with console.status("[bold green]Analyzing code...[/bold green]"):
        all_smells = detector.detect_all()

    # Filter by severity
    if severity != "all":
        severity_level = CodeSmellSeverity[severity.upper()]
        all_smells = [smell for smell in all_smells if smell.severity.value >= severity_level.value]

    # Filter by category
    if category != "all":
        category_map = {
            "bloaters": CodeSmellCategory.BLOATERS,
            "object_orientation_abusers": CodeSmellCategory.OBJECT_ORIENTATION_ABUSERS,
            "change_preventers": CodeSmellCategory.CHANGE_PREVENTERS,
            "dispensables": CodeSmellCategory.DISPENSABLES,
            "couplers": CodeSmellCategory.COUPLERS,
        }
        category_enum = category_map[category]
        all_smells = [smell for smell in all_smells if smell.category == category_enum]

    # Display results
    if not all_smells:
        console.print("[bold green]No code smells detected![/bold green]")
        return

    console.print(f"[bold yellow]Detected {len(all_smells)} code smells:[/bold yellow]")

    # Group by category
    smells_by_category: dict[CodeSmellCategory, list[CodeSmell]] = {}
    for smell in all_smells:
        if smell.category not in smells_by_category:
            smells_by_category[smell.category] = []
        smells_by_category[smell.category].append(smell)

    # Create a tree view of the results
    tree = Tree("[bold]Code Smells by Category[/bold]")
    for category, smells in smells_by_category.items():
        category_node = tree.add(f"[bold]{category.name}[/bold] ({len(smells)} issues)")

        # Group by severity within each category
        smells_by_severity: dict[CodeSmellSeverity, list[CodeSmell]] = {}
        for smell in smells:
            if smell.severity not in smells_by_severity:
                smells_by_severity[smell.severity] = []
            smells_by_severity[smell.severity].append(smell)

        # Add severity nodes
        for severity, severity_smells in sorted(smells_by_severity.items(), key=lambda x: x[0].value, reverse=True):
            severity_color = {
                CodeSmellSeverity.LOW: "green",
                CodeSmellSeverity.MEDIUM: "yellow",
                CodeSmellSeverity.HIGH: "orange",
                CodeSmellSeverity.CRITICAL: "red",
            }[severity]

            severity_node = category_node.add(f"[bold {severity_color}]{severity.name}[/bold {severity_color}] ({len(severity_smells)} issues)")

            # Add individual smells
            for smell in severity_smells:
                refactorable = " [bold green](auto-refactorable)[/bold green]" if refactorer.can_refactor(smell) else ""
                severity_node.add(f"{smell.symbol.name}: {smell.description}{refactorable}")

    console.print(tree)

    # Refactor if requested
    if refactor:
        refactorable_smells = [smell for smell in all_smells if refactorer.can_refactor(smell)]

        if not refactorable_smells:
            console.print("[bold yellow]No automatically refactorable code smells found.[/bold yellow]")
        else:
            console.print(f"[bold blue]Refactoring {len(refactorable_smells)} code smells...[/bold blue]")

            with console.status("[bold green]Refactoring code...[/bold green]"):
                results = refactorer.refactor_all(refactorable_smells)

            # Display refactoring results
            success_count = sum(1 for success in results.values() if success)
            console.print(f"[bold green]Successfully refactored {success_count}/{len(results)} code smells.[/bold green]")

            if success_count < len(results):
                console.print("[bold yellow]Some refactorings failed. See details below:[/bold yellow]")
                for smell, success in results.items():
                    if not success:
                        console.print(f"[bold red]Failed to refactor:[/bold red] {smell}")

    # Output JSON report if requested
    if output:
        report = {
            "summary": {
                "total_smells": len(all_smells),
                "by_category": {category.name: len(smells) for category, smells in smells_by_category.items()},
                "by_severity": {severity.name: len([s for s in all_smells if s.severity == severity]) for severity in CodeSmellSeverity},
                "refactorable": len([s for s in all_smells if refactorer.can_refactor(s)]),
            },
            "smells": [
                {
                    "name": smell.name,
                    "description": smell.description,
                    "category": smell.category.name,
                    "severity": smell.severity.name,
                    "symbol": smell.symbol.name,
                    "file": smell.symbol.file.path if hasattr(smell.symbol, "file") and smell.symbol.file else None,
                    "refactoring_suggestions": smell.refactoring_suggestions,
                    "can_auto_refactor": refactorer.can_refactor(smell),
                }
                for smell in all_smells
            ],
        }

        # Write the report
        with open(output, "w") as f:
            json.dump(report, f, indent=2)

        console.print(f"[bold blue]Report written to [cyan]{output}[/cyan][/bold blue]")
