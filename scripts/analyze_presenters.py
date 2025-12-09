#!/usr/bin/env python3
"""Analyze presenter files to identify properties in the vm method that are simple repeats.

This script searches for presenter files in a specified directory, analyzes the vm method
in each file, and identifies properties that are simple repeats of the input properties.

Usage:
    python analyze_presenters.py [directory_path]

If no directory path is provided, the script will search in the current directory.
"""

import json
import os
import re
import sys


class PresenterAnalyzer:
    """Analyzes presenter files to find properties in vm method that are simple repeats."""

    def __init__(self, directory: str = "."):
        self.directory = directory
        self.presenter_files = []
        self.results = {}

    def find_presenter_files(self) -> list[str]:
        """Find all presenter files in the specified directory."""
        presenter_files = []

        for root, _, files in os.walk(self.directory):
            for file in files:
                # Look for files that might be presenters
                if (file.endswith(".ts") or file.endswith(".tsx") or file.endswith(".js") or file.endswith(".jsx")) and "presenter" in file.lower():
                    presenter_files.append(os.path.join(root, file))

        self.presenter_files = presenter_files
        return presenter_files

    def analyze_presenter_file(self, file_path: str) -> dict[str, list[str]]:
        """Analyze a presenter file to find properties in vm method that are simple repeats."""
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Parse the file to find the vm method
        try:
            # Look for vm method
            vm_method_match = re.search(r"vm\s*\([^)]*\)\s*{([^}]*)}", content, re.DOTALL)

            if not vm_method_match:
                # Try alternative pattern for arrow functions
                vm_method_match = re.search(r"vm\s*=\s*\([^)]*\)\s*=>\s*{([^}]*)}", content, re.DOTALL)

            if not vm_method_match:
                # Try alternative pattern for object methods in JS/TS
                vm_method_match = re.search(r"vm\s*\([^)]*\)\s*{([^}]*return[^}]*})", content, re.DOTALL)

            if not vm_method_match:
                return {}

            vm_method_body = vm_method_match.group(1)

            # Look for object properties in the return statement
            return_match = re.search(r"return\s*{([^}]*)}", vm_method_body, re.DOTALL)

            if not return_match:
                return {}

            return_body = return_match.group(1)

            # Extract properties
            properties = {}
            prop_matches = re.finditer(r"(\w+)\s*:\s*([^,]+)", return_body)

            for match in prop_matches:
                prop_name = match.group(1).strip()
                prop_value = match.group(2).strip()

                # Check if the property value is a simple repeat (same name as property)
                if prop_value == prop_name:
                    if "simple_repeats" not in properties:
                        properties["simple_repeats"] = []
                    properties["simple_repeats"].append(prop_name)

            return properties

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
            return {}

    def analyze_all_presenters(self) -> dict[str, dict[str, list[str]]]:
        """Analyze all presenter files and collect results."""
        if not self.presenter_files:
            self.find_presenter_files()

        results = {}

        for file_path in self.presenter_files:
            file_results = self.analyze_presenter_file(file_path)
            if file_results:
                results[file_path] = file_results

        self.results = results
        return results

    def print_results(self):
        """Print the analysis results in a readable format."""
        if not self.results:
            self.analyze_all_presenters()

        if not self.results:
            print("No presenter files found or no simple repeats identified.")
            return

        print("\nAnalysis Results:")
        print("================\n")

        for file_path, file_results in self.results.items():
            print(f"File: {file_path}")

            if "simple_repeats" in file_results:
                print("  Simple Repeats:")
                for prop in file_results["simple_repeats"]:
                    print(f"    - {prop}")

            print()

    def generate_report(self, output_file: str = "presenter_analysis_report.json"):
        """Generate a JSON report of the analysis results."""
        if not self.results:
            self.analyze_all_presenters()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2)

        print(f"Report generated: {output_file}")


def main():
    """Main function to run the script."""
    directory = "."
    if len(sys.argv) > 1:
        directory = sys.argv[1]

    analyzer = PresenterAnalyzer(directory)
    analyzer.find_presenter_files()

    if not analyzer.presenter_files:
        print(f"No presenter files found in {directory}")
        return

    print(f"Found {len(analyzer.presenter_files)} presenter files:")
    for file in analyzer.presenter_files:
        print(f"  - {file}")

    analyzer.analyze_all_presenters()
    analyzer.print_results()
    analyzer.generate_report()


if __name__ == "__main__":
    main()
