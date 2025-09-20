from pydantic import BaseModel
from pydantic.fields import Field

import codegen.sdk.cli.sdk.decorator
from codegen.sdk.cli.utils.count_functions_2 import NumberType

# from app.codemod.compilation.models.context import CodemodContext
# from app.codemod.compilation.models.pr_options import PROptions
# from codegen.sdk import PyCodebaseType

# context: CodemodContext


class CountFunctionsArgs(BaseModel):
    number_attr: NumberType
    string_attr: str
    boolean_attr: bool
    list_attr: list[str]
    dict_attr: dict[str, str]
    complex_attr: str = Field(default_factory=lambda: "hello")


@codegen.sdk.cli.sdk.decorator.function("count-functions")
def run(codebase, pr_options, arguments: CountFunctionsArgs):
    # Count Functions in Codebase

    # Initialize a total function counter
    total_functions = 0

    # Optionally, track functions by directory for more insight
    functions_by_directory = {}

    # Iterate over all functions in the codebase
    for function in codebase.functions:
        total_functions += 1

        # Extract directory from function's file path
        directory = function.file.filepath.split("/")[0]
        functions_by_directory[directory] = functions_by_directory.get(directory, 0) + 1

    # Print the results
    print(f"🔢 Total Functions: {total_functions}")
    print("\n📂 Functions by Directory:")
    for directory, count in sorted(functions_by_directory.items(), key=lambda x: x[1], reverse=True):
        print(f"  {directory}: {count} functions")
