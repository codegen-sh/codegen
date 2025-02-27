import json
from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP

from codegen.extensions.tools import reveal_symbol
from codegen.extensions.tools.search import search
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

mcp = FastMCP(
    "codebase-tools-mcp",
    instructions="""Use this server to access any information from your codebase. This tool can provide information ranging from AST Symbol details and information from across the codebase.
    Use this tool for all questions, queries regarding your codebase.""",
)


@mcp.tool(name="reveal_symbol", description="Reveal the dependencies and usages of a symbol up to N degrees")
def reveal_symbol_tool(
    symbol_name: Annotated[str, "Name of the symbol to inspect"],
    target_file: Annotated[Optional[str], "The file path of the file containing the symbol to inspect"],
    codebase_dir: Annotated[str, "The root directory of your codebase"],
    codebase_language: Annotated[ProgrammingLanguage, "The language the codebase is written in"],
    max_depth: Annotated[Optional[int], "depth up to which symbol information is retrieved"],
    collect_dependencies: Annotated[Optional[bool], "includes dependencies of symbol"],
    collect_usages: Annotated[Optional[bool], "includes usages of symbol"],
):
    codebase = Codebase(repo_path=codebase_dir, language=codebase_language)
    result = reveal_symbol(
        codebase=codebase,
        symbol_name=symbol_name,
        filepath=target_file,
        max_depth=max_depth,
        collect_dependencies=collect_dependencies,
        collect_usages=collect_usages,
    )
    return json.dumps(result, indent=2)


@mcp.tool(name="search_codebase", description="The search query to find in the codebase. When ripgrep is available, this will be passed as a ripgrep pattern. For regex searches, set use_regex=True")
def search_codebase_tool(
    query: Annotated[str, "The search query to find in the codebase. When ripgrep is available, this will be passed as a ripgrep pattern. For regex searches, set use_regex=True."],
    codebase_dir: Annotated[str, "The root directory of your codebase"],
    codebase_language: Annotated[ProgrammingLanguage, "The language the codebase is written in"],
    target_directories: Annotated[Optional[list[str]], "list of directories to search within"] = None,
    file_extensions: Annotated[Optional[list[str]], "list of file extensions to search (e.g. ['.py', '.ts'])"] = None,
    page: Annotated[int, "page number to return (1-based)"] = 1,
    files_per_page: Annotated[int, "number of files to return per page"] = 10,
    use_regex: Annotated[bool, "use regex for the search query"] = False,
):
    codebase = Codebase(repo_path=codebase_dir, language=codebase_language)
    result = search(codebase, query, target_directories=target_directories, file_extensions=file_extensions, page=page, files_per_page=files_per_page, use_regex=use_regex)
    return json.dumps(result, indent=2)


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codebase tools server...")
    mcp.run(transport="stdio")
