import asyncio
from dataclasses import dataclass, field
from typing import Annotated, Optional, Dict, Any, List
from mcp.server.fastmcp import FastMCP
from codegen import Codebase


@dataclass
class CodebaseState:
    """Class to manage codebase state and parsing."""

    parse_task: Optional[asyncio.Future] = None
    parsed_codebase: Optional[Codebase] = None
    codebase_path: Optional[str] = None
    log_buffer: List[str] = field(default_factory=list)

    async def parse(self, path: str) -> Codebase:
        """Parse the codebase at the given path."""
        codebase = Codebase(path)
        self.parsed_codebase = codebase
        self.codebase_path = path
        return codebase

    def reset(self) -> None:
        """Reset the state."""
        if self.parsed_codebase:
            self.parsed_codebase.reset()
        self.log_buffer.clear()


# Initialize FastMCP server
mcp = FastMCP(
    "codegen-mcp-server",
    instructions="""This server provides tools to parse and modify a codebase using codemods.
    It can initiate parsing, check parsing status, and execute codemods.""",
)

# Initialize state
state = CodebaseState()


def capture_output(*args, **kwargs) -> None:
    """Capture and log output messages."""
    for arg in args:
        state.log_buffer.append(str(arg))


@mcp.tool(name="parse_codebase", description="Initiate codebase parsing")
async def parse_codebase(codebase_path: Annotated[str, "path to the codebase to be parsed"]) -> Dict[str, str]:
    if not state.parse_task or state.parse_task.done():
        state.parse_task = asyncio.get_event_loop().run_in_executor(None, lambda: state.parse(codebase_path))
        return {"message": "Codebase parsing initiated, this may take some time depending on the size of the codebase. Use the `check_parsing_status` tool to check if the parse has completed."}
    return {"message": "Codebase is already being parsed."}


@mcp.tool(name="check_parse_status", description="Check if codebase parsing has completed")
async def check_parse_status() -> Dict[str, str]:
    if not state.parse_task:
        return {"message": "No codebase provided to parse."}
    if state.parse_task.done():
        return {"message": "Codebase parsing completed."}
    return {"message": "Codebase parsing in progress."}


@mcp.tool(name="execute_codemod", description="Execute a codemod on the codebase")
async def execute_codemod(codemod: Annotated[str, "The python codemod code to execute on the codebase"]) -> Dict[str, Any]:
    if not state.parse_task or not state.parse_task.done():
        return {"error": "Codebase is not ready for codemod execution."}

    try:
        await state.parse_task
        # TODO: Implement proper sandboxing for code execution
        context = {
            "codebase": state.parsed_codebase,
            "print": capture_output,
        }
        exec(codemod, context)

        logs = "\n".join(state.log_buffer)

        state.reset()
        return {"message": "Codemod executed and codebase reset.", "logs": logs}
    except Exception as e:
        return {"error": f"Error executing codemod: {str(e)}", "details": {"type": type(e).__name__, "message": str(e)}}


def main():
    print("starting codegen-mcp-server")
    run = mcp.run_stdio_async()
    print("codegen-mcp-server started")
    asyncio.get_event_loop().run_until_complete(run)


if __name__ == "__main__":
    main()
