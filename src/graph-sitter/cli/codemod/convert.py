from textwrap import indent


def convert_to_cli(input: str, language: str, name: str) -> str:
    return f"""
# Run this codemod using `gs run {name}` OR the `run_codemod` MCP tool.
# Important: if you run this as a regular python file, you MUST run it such that
#  the base directory './' is the base of your codebase, otherwise it will not work.
import codegen.sdk
from codegen.sdk.core.codebase import Codebase


@codegen.sdk.function('{name}')
def run(codebase: Codebase):
{indent(input, "    ")}


if __name__ == "__main__":
    print('Parsing codebase...')
    codebase = Codebase("./")

    print('Running function...')
    codegen.run(run)
"""


def convert_to_ui(input: str) -> str:
    return input
