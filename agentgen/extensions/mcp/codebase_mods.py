import json
import os
from typing import Annotated

from mcp.server.fastmcp import FastMCP

from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

mcp = FastMCP(
    "codebase-mods-mcp",
    instructions="Use this server to invoke deterministic codemods for your codebase. This implements a variety of codemods to be used to modify your codebase to your satisfaction",
)


@mcp.tool(name="split_files_by_function", description="split out the functions in defined in the provided file into new files")
def split_files_by_function(
    target_file: Annotated[str, "file path to the target file to split"],
    codebase_dir: Annotated[str, "Absolute path to the codebase root directory. It is highly encouraged to provide the root codebase directory and not a sub directory"],
    codebase_language: Annotated[ProgrammingLanguage, "The language the codebase is written in"],
):
    if not os.path.exists(codebase_dir):
        return {"error": f"Codebase directory '{codebase_dir}' does not exist. Please provide a valid directory path."}
    codebase = Codebase(repo_path=codebase_dir, language=codebase_language)
    new_files = {}
    file = codebase.get_file(target_file)
    # for each test_function in the file
    for function in file.functions:
        # Create a new file for each test function using its name
        new_file = codebase.create_file(f"{file.directory.path}/{function.name}.py", sync=False)

        print(f"🚠 🚠 Moving `{function.name}` to new file `{new_file.name}`")
        # Move the test function to the newly created file
        function.move_to_file(new_file)
        new_files[new_file.filepath] = [function.name]

    codebase.commit()

    result = {"description": "the following new files have been created with each with containing the function specified", "new_files": new_files}

    return json.dumps(result, indent=2)


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codebase mods server...")
    mcp.run(transport="stdio")
