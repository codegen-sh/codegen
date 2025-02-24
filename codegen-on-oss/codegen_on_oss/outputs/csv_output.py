import csv
import os
from pathlib import Path
from typing import Any

from codegen_on_oss.outputs.base import BaseOutput


class CSVOutput(BaseOutput):
    """
    CSVOutput is a class that writes output to a CSV file.
    """

    def __init__(self, fields: list[str], output_path: str):
        super().__init__(fields)
        self.output_path = output_path

    def write_output(self, value: dict[str, Any]):
        """
        Writes a dictionary to a CSV file. If the file does not exist, it creates it and writes headers; otherwise, it appends.
        """
        file_exists = os.path.isfile(self.output_path)
        if not file_exists:
            Path(self.output_path).parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, mode="a", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.fields)
            if not file_exists:
                writer.writeheader()
            writer.writerow(value)
