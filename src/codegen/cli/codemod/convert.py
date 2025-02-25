from textwrap import indent


def convert_to_cli(input: str, language: str, name: str) -> str:
    return f"""import codegen
from codegen import Codebase


@codegen.function('{name}')
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
