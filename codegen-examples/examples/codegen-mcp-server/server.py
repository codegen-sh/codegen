import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

import requests
from codegen import Codebase
from codegen.cli.api.client import RestAPI
from codegen.cli.api.endpoints import CODEGEN_SYSTEM_PROMPT_URL
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.codemod.convert import convert_to_cli
from codegen.cli.utils.default_code import DEFAULT_CODEMOD
from mcp.server.fastmcp import FastMCP


@dataclass
class CodebaseState:
    """Class to manage codebase state and parsing."""

    parse_task: Optional[asyncio.Future] = None
    parsed_codebase: Optional[Codebase] = None
    log_buffer: List[str] = field(default_factory=list)
    codemod_tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    def parse(self, path: str) -> Codebase:
        """Parse the codebase at the given path."""
        codebase = Codebase(path)
        self.parsed_codebase = codebase
        return codebase

    def reset(self) -> None:
        """Reset the state."""
        self.log_buffer.clear()


# Initialize FastMCP server
mcp = FastMCP(
    "codegen-mcp-server",
    instructions="""This server provides tools to parse and modify a codebase using codemods.
    It can initiate parsing, check parsing status, and execute codemods.""",
    dependencies=["codegen"],
)

# Initialize state
state = CodebaseState()


def capture_output(*args, **kwargs) -> None:
    """Capture and log output messages."""
    for arg in args:
        state.log_buffer.append(str(arg))


def update_codebase(future: asyncio.Future):
    try:
        result = future.result()
        if result is not None:
            state.parsed_codebase = result
        else:
            state.parsed_codebase = None
    except Exception:
        pass


async def create_codemod_task(name: str, description: str, language: str = "python") -> Dict[str, Any]:
    """Background task to create a codemod using the API."""
    try:
        # Convert name to snake case for filename
        name_snake = name.lower().replace("-", "_").replace(" ", "_")

        # Create path within .codegen/codemods
        codemods_dir = Path(".codegen") / "codemods"
        function_dir = codemods_dir / name_snake
        codemod_path = function_dir / f"{name_snake}.py"
        prompt_path = function_dir / f"{name_snake}-system-prompt.txt"

        # Create directories if they don't exist
        function_dir.mkdir(parents=True, exist_ok=True)

        # Use API to generate implementation if description is provided
        if description:
            try:
                api = RestAPI(get_current_token())
                response = api.create(name=name, query=description)
                code = convert_to_cli(response.code, language, name)
                context = response.context

                # Save the prompt/context
                if context:
                    prompt_path.write_text(context)
            except Exception as e:
                # Fall back to default implementation on API error
                code = DEFAULT_CODEMOD.format(name=name)
                return {"status": "error", "message": f"Error generating codemod via API, using default template: {str(e)}", "path": str(codemod_path), "code": code}
        else:
            # Use default implementation
            code = DEFAULT_CODEMOD.format(name=name)

        # Write the codemod file
        codemod_path.write_text(code)

        # Download and save system prompt if not already done
        if not prompt_path.exists():
            try:
                response = requests.get(CODEGEN_SYSTEM_PROMPT_URL)
                response.raise_for_status()
                prompt_path.write_text(response.text)
            except Exception:
                pass  # Ignore system prompt download failures

        return {"status": "completed", "message": f"Created codemod '{name}'", "path": str(codemod_path), "docs_path": str(prompt_path), "code": code}
    except Exception as e:
        return {"status": "error", "message": f"Error creating codemod: {str(e)}"}


@mcp.tool(name="parse_codebase", description="Initiate codebase parsing")
async def parse_codebase(codebase_path: Annotated[str, "path to the codebase to be parsed"]) -> Dict[str, str]:
    if not state.parse_task or state.parse_task.done():
        state.parse_task = asyncio.get_event_loop().run_in_executor(None, lambda: state.parse(codebase_path))
        state.parse_task.add_done_callback(update_codebase)
        return {"message": "Codebase parsing initiated, this may take some time depending on the size of the codebase. Use the `check_parse_status` tool to check if the parse has completed."}
    return {"message": "Codebase is already being parsed.", "status": "error"}


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
        if state.parsed_codebase is None:
            return {"error": "Codebase path is not set."}
        else:
            # TODO: Implement proper sandboxing for code execution
            context = {
                "codebase": state.parsed_codebase,
                "print": capture_output,
            }
            exec(codemod, context)

        logs = "\n".join(state.log_buffer)
        state.reset()
        return {"message": "Codemod executed, view the logs for any output and your source code for any resulting updates.", "logs": logs}
    except Exception as e:
        return {"error": f"Error executing codemod: {str(e)}", "details": {"type": type(e).__name__, "message": str(e)}}


@mcp.tool(name="create_codemod", description="Initiate creation of a new codemod in the .codegen directory")
async def create_codemod(
    name: Annotated[str, "Name of the codemod to create"],
    description: Annotated[str, "Description of what the codemod does"] = None,
    language: Annotated[str, "Programming language for the codemod"] = "python",
) -> Dict[str, Any]:
    # Check if a task with this name already exists
    if name in state.codemod_tasks:
        task_info = state.codemod_tasks[name]
        if task_info["task"].done():
            result = task_info["task"].result()
            # Clean up completed task
            del state.codemod_tasks[name]
            return result
        else:
            return {"status": "in_progress", "message": f"Codemod '{name}' creation is already in progress. Use view_codemods to check status."}

    # Create a task that runs in a separate thread using run_in_executor
    loop = asyncio.get_event_loop()

    # We need to wrap our async function in a sync function for run_in_executor
    def sync_wrapper():
        # Create a new event loop for this thread
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        # Run our async function to completion in this thread
        return new_loop.run_until_complete(create_codemod_task(name, description, language))

    # Run the wrapper in a thread pool
    task = loop.run_in_executor(None, sync_wrapper)

    # Store task info
    state.codemod_tasks[name] = {"task": task, "name": name, "description": description, "language": language, "started_at": loop.time()}

    # Return immediately
    return {"status": "initiated", "message": f"Codemod '{name}' creation initiated. Use view_codemods to check status."}


@mcp.tool(name="view_codemods", description="View all codemods and their creation status")
async def view_codemods() -> Dict[str, Any]:
    result = {"active_tasks": {}, "available_codemods": []}

    # Check active tasks
    current_time = asyncio.get_event_loop().time()
    for name, task_info in list(state.codemod_tasks.items()):
        task = task_info["task"]
        elapsed = current_time - task_info["started_at"]

        if task.done():
            # Task completed, get result
            try:
                task_result = task.result()
                # Clean up completed task
                del state.codemod_tasks[name]
                result["active_tasks"][name] = {"status": task_result.get("status", "completed"), "message": task_result.get("message", "Completed"), "elapsed_seconds": round(elapsed, 1)}
            except Exception as e:
                result["active_tasks"][name] = {"status": "error", "message": f"Error: {str(e)}", "elapsed_seconds": round(elapsed, 1)}
                # Clean up failed task
                del state.codemod_tasks[name]
        else:
            # Task still running
            result["active_tasks"][name] = {"status": "in_progress", "message": "Creation in progress...", "elapsed_seconds": round(elapsed, 1)}

    # Find existing codemods
    try:
        codemods_dir = Path(".codegen") / "codemods"
        if codemods_dir.exists():
            for codemod_dir in codemods_dir.iterdir():
                if codemod_dir.is_dir():
                    codemod_file = codemod_dir / f"{codemod_dir.name}.py"
                    if codemod_file.exists():
                        result["available_codemods"].append({"name": codemod_dir.name, "path": str(codemod_file)})
    except Exception as e:
        result["error"] = f"Error listing codemods: {str(e)}"

    return result


@mcp.tool(name="run_codemod", description="Run a codemod from the .codegen directory")
async def run_codemod(
    name: Annotated[str, "Name of the codemod to run"],
    arguments: Annotated[str, "JSON string of arguments to pass to the codemod"] = None,
) -> Dict[str, Any]:
    if not state.parse_task or not state.parse_task.done():
        return {"error": "Codebase is not ready for codemod execution. Parse a codebase first."}

    try:
        # Wait for codebase to be ready
        await state.parse_task
        if state.parsed_codebase is None:
            return {"error": "Codebase path is not set."}

        # Get the codemod using CodemodManager
        try:
            from codegen.cli.utils.codemod_manager import CodemodManager

            codemod = CodemodManager.get_codemod(name)
        except Exception as e:
            return {"error": f"Error loading codemod '{name}': {str(e)}"}

        # Parse arguments if provided
        args_dict = None
        if arguments:
            try:
                args_dict = json.loads(arguments)

                # Validate arguments if schema exists
                if codemod.arguments_type_schema:
                    from codegen.cli.utils.json_schema import validate_json

                    if not validate_json(codemod.arguments_type_schema, args_dict):
                        return {"error": f"Invalid arguments format. Expected schema: {codemod.arguments_type_schema}"}
            except json.JSONDecodeError:
                return {"error": "Invalid JSON in arguments parameter"}

        # Create a session for the codemod
        from codegen.cli.auth.session import CodegenSession

        session = CodegenSession(state.parsed_codebase.path)
        session.codebase = state.parsed_codebase

        # Capture output
        original_print = print
        import builtins

        builtins.print = capture_output

        try:
            # Run the codemod using run_local
            from codegen.cli.commands.run.run_local import run_local

            run_local(session, codemod, diff_preview=None, arguments=args_dict)

            # Collect logs
            logs = "\n".join(state.log_buffer)
            state.reset()

            return {"message": f"Codemod '{name}' executed successfully", "logs": logs, "codemod_path": str(codemod.path), "result": "Codemod applied successfully"}
        finally:
            # Restore original print
            builtins.print = original_print

    except Exception as e:
        return {"error": f"Error executing codemod: {str(e)}", "details": {"type": type(e).__name__, "message": str(e)}}


def main():
    print("starting codegen-mcp-server")
    run = mcp.run_stdio_async()
    print("codegen-mcp-server started")
    asyncio.get_event_loop().run_until_complete(run)


if __name__ == "__main__":
    main()
