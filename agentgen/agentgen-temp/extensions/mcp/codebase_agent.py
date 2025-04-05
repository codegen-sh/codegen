import os
from typing import Annotated

from mcp.server.fastmcp import FastMCP

from codegen.extensions.langchain.agent import create_codebase_inspector_agent
from codegen.sdk.core.codebase import Codebase
from codegen.shared.enums.programming_language import ProgrammingLanguage

# Initialize FastMCP server

mcp = FastMCP(
    "codebase-agent-mcp",
    instructions="""Use this server to access any information from your codebase. This tool can provide information ranging from AST Symbol details and information from across the codebase.
    Use this tool for all questions, queries regarding your codebase.""",
)


@mcp.tool(name="query_codebase", description="Query your codebase for information about symbols, dependencies, files, anything")
def query_codebase(
    query: Annotated[
        str, "A question or prompt requesting information about or on some aspect of your codebase, for example 'find all usages of the method 'foobar', include as much information as possible"
    ],
    codebase_dir: Annotated[str, "Absolute path to the codebase root directory. It is highly encouraged to provide the root codebase directory and not a sub directory"],
    codebase_language: Annotated[ProgrammingLanguage, "The language the codebase is written in"],
):
    # Input validation
    if not query or not query.strip():
        return {"error": "Query cannot be empty"}

    if not codebase_dir or not codebase_dir.strip():
        return {"error": "Codebase directory path cannot be empty"}

    # Check if codebase directory exists
    if not os.path.exists(codebase_dir):
        return {"error": f"Codebase directory '{codebase_dir}' does not exist. Please provide a valid directory path."}

    try:
        # Initialize codebase
        codebase = Codebase(repo_path=codebase_dir, language=codebase_language)

        # Create the agent
        agent = create_codebase_inspector_agent(codebase=codebase, model_provider="openai", model_name="gpt-4o")

        result = agent.invoke({"input": query}, config={"configurable": {"thread_id": 1}})

        return result["messages"][-1].content

    except Exception as e:
        return {"error": f"An error occurred while processing the request: {e!s}"}


if __name__ == "__main__":
    # Initialize and run the server
    print("Starting codebase agent server...")
    mcp.run(transport="stdio")
