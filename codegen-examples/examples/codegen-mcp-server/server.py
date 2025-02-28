import asyncio
import functools
import json
from dataclasses import dataclass, field
from logging import getLogger
from pathlib import Path
from typing import Annotated, Any, Dict, List, Optional

import requests
from codegen import Codebase
from codegen.cli.api.client import RestAPI
from codegen.cli.api.endpoints import CODEGEN_SYSTEM_PROMPT_URL
from codegen.cli.auth.token_manager import get_current_token
from codegen.cli.codemod.convert import convert_to_cli
from codegen.cli.utils.default_code import DEFAULT_CODEMOD
from codegen.extensions.tools.reveal_symbol import reveal_symbol
from mcp.server.fastmcp import FastMCP

logger = getLogger(__name__)

################################################################################
# State + Server Definition
################################################################################
REPO_PATH = "/Users/jonhack/CS/CODEGEN/codegen-sdk"


@dataclass
class CodebaseState:
    """Class to manage codebase state and parsing."""

    parsed_codebase: Optional[Codebase] = None
    log_buffer: List[str] = field(default_factory=list)
    codemod_tasks: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    codebase_path: str = "."

    def __post_init__(self):
        """Initialize by parsing the codebase immediately."""
        self.parse(self.codebase_path)

    def parse(self, path: str) -> None:
        """Parse the codebase at the given path."""
        try:
            self.codebase_path = path
            self.parsed_codebase = Codebase(path, language="python")
        except Exception:
            self.parsed_codebase = None

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

# Initialize state with a specific path
state = CodebaseState(codebase_path=REPO_PATH)


def capture_output(*args, **kwargs) -> None:
    """Capture and log output messages."""
    for arg in args:
        state.log_buffer.append(str(arg))


# Decorator to require codebase to be parsed
def requires_parsed_codebase(func):
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        if state.parsed_codebase is None:
            return {"error": "Codebase has not been parsed successfully. Please run parse_codebase first."}
        return await func(*args, **kwargs)

    return wrapper


# @mcp.tool(name="parse_codebase", description="Parse the codebase at the specified path")
# async def parse_codebase(codebase_path: Annotated[str, "path to the codebase to be parsed. Usually this is just '.'"]) -> Dict[str, str]:
#     try:
#         print(f"Parsing codebase at {codebase_path}...")
#         state.parse(codebase_path)
#         if state.parsed_codebase:
#             return {"message": f"Codebase parsed successfully. Found {len(state.parsed_codebase.files)} files.", "status": "success"}
#         else:
#             return {"message": "Codebase parsing failed.", "status": "error"}
#     except Exception as e:
#         return {"message": f"Error parsing codebase: {str(e)}", "status": "error"}


# @mcp.tool(name="check_parse_status", description="Check if codebase is parsed")
# async def check_parse_status() -> Dict[str, str]:
#     if state.parsed_codebase is None:
#         return {"message": "Codebase has not been parsed successfully.", "status": "not_parsed"}
#     return {"message": f"Codebase is parsed. Found {len(state.parsed_codebase.files)} files.", "status": "parsed"}


async def create_codemod_task(name: str, description: str, language: str = "python") -> Dict[str, Any]:
    """Background task to create a codemod using the API."""
    try:
        # Convert name to snake case for filename
        name_snake = name.lower().replace("-", "_").replace(" ", "_")

        # Create path within .codegen/codemods
        codemods_dir = REPO_PATH / Path(".codegen") / "codemods"
        function_dir = codemods_dir / name_snake
        codemod_path = function_dir / f"{name_snake}.py"
        prompt_path = function_dir / f"{name_snake}-system-prompt.txt"

        # Create directories if they don't exist
        logger.info(f"Creating directories for codemod {name} in {function_dir}")
        function_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directories for codemod {name} in {function_dir}")

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


################################################################################
# Prompts
################################################################################


@mcp.prompt()
def codegen_system_prompt():
    """System prompt for the codegen server"""
    return """
Codegen is a tool for programmatically manipulating codebases via "codemods".

It provides a scriptable interface to a powerful, multi-lingual language server built on top of Tree-sitter.

For example, consider the following script:

```python
from codegen import Codebase

# Codegen builds a complete graph connecting
# functions, classes, imports and their relationships
codebase = Codebase("./")

# Work with code without dealing with syntax trees or parsing
for function in codebase.functions:
    # Comprehensive static analysis for references, dependencies, etc.
    if not function.usages:
        # Auto-handles references and imports to maintain correctness
        function.remove()

# Fast, in-memory code index
codebase.commit()
```

This script will remove all functions that are not used in the codebase.

You can run this script using the `run_codemod` tool.

# Developing Codemods

Codegen codemods are functions that take a `Codebase` as input and manipulate it.

They live in the `.codegen/codemods/{name}/{name.py}` directory, and take the following form:
```python
from codegen import Codebase

@codegen.function('{name}')
def codemod(codebase: Codebase):
    for function in codebase.functions:
        if not function.usages:
            print(f"🗑️ Removing: {function.name}")
            function.remove()
```

You can run these codemods using the `run_codemod` tool and modify the codemod behavior by editing the `{name}.py` file.

## Developer Flow

Typically, developers will need to iterate on a codemod until it is working as expected.

The developer flow typically consists of the following steps:

1. Create a new codemod using the `create_codemod` tool.
    - This will create a new codemod in the `.codegen/codemods/{name}` directory.
    - The codemod will be created with an initial implementation created by an expert LLM
    - It will also included documentation in a text file, containing similar examples and explanations of relevant syntax.
    - You have to wait until the `view_codemods` tool shows the codemod as `completed` before you can run it!
2. Run the codemod using the `run_codemod` tool
    - This will run the codemod on the codebase
    - Logs (print statements) will be captured and displayed in the response
    - All changes will be written to the file system
3. Inspect the results using the `git diff` command or similar
    - This will show the changes that were made to the codebase.
4. Reset the codebase to the previous state using the `reset` tool
    - This will preserve all files in the `.codegen` directory, allowing you to re-run the codemod and inspect the results.
5. Modify the codemod until it is working as expected
    - This can be done by editing the `{name}.py` file directly
    - Then proceed to step 2 again!

## Async APIs

Two actions take ~10s and will trigger MCP timeouts if they are performed synchronously:

1. `create_codemod`
2. `parse_codebase`


Therefore, both of these have associated tools that will initiate the action in a background thread, and return immediately.

You can use the `view_codemods` tool to check the status of these background tasks.

Similarly, you can use the `view_parse_status` tool to check the status of the codebase parsing task.

## Helpful Tips

- Only develop codemods on a clean commit
  - This ensures that you can return to a working state by calling `reset`
  - Otherwise, `reset` will blow away all of your non-codemod changes!


"""


@mcp.resource("config://app")
def get_config() -> str:
    """Static configuration data"""
    return "App configuration here"


################################################################################
# MCP Server Tools
################################################################################


@mcp.tool(name="create_codemod", description="Initiate creation of a new codemod in the `.codegen/codemods/{name}` directory")
async def create_codemod(
    name: Annotated[str, "Name of the codemod to create"],
    description: Annotated[str, "Description of what the codemod does. Be specific, as this is passed to an expert LLM to generate the first draft"] = None,
    language: Annotated[str, "Programming language for the codemod (default Python)"] = "python",
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
    return {
        "status": "initiated",
        "message": f"""
Codemod '{name}' creation initiated.

Next steps:
- Use `view_codemods` tool to check status
- Use `run_codemod` tool to run the codemod. Important! Use this tool instead of directly executing the codemod file - this ensures it uses a properly-parsed codebase.
- Use `reset` tool to revert to the current state of the codebase if you need to make modifications to the codemod itself.
""",
    }


@mcp.tool(name="view_codemods", description="View all available codemods and their creation status")
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
        codemods_dir = REPO_PATH / Path(".codegen") / "codemods"
        if codemods_dir.exists():
            for codemod_dir in codemods_dir.iterdir():
                if codemod_dir.is_dir():
                    codemod_file = codemod_dir / f"{codemod_dir.name}.py"
                    if codemod_file.exists():
                        result["available_codemods"].append({"name": codemod_dir.name, "path": str(codemod_file), "run_with": f"run_codemod('{codemod_dir.name}')"})
    except Exception as e:
        result["error"] = f"Error listing codemods: {str(e)}"

    return result


@mcp.tool(name="run_codemod", description="Runs a codemod from the `.codegen/codemods/{name}` directory and writes output to disk")
async def run_codemod(
    name: Annotated[str, "Name of the codemod to run"],
    arguments: Annotated[str, "JSON string of arguments to pass to the codemod"] = None,
) -> Dict[str, Any]:
    if not state.parsed_codebase:
        return {"error": "Codebase is not ready for codemod execution. Parse a codebase first."}

    try:
        # Get the codemod using CodemodManager
        try:
            from codegen.cli.utils.codemod_manager import CodemodManager

            codemod = CodemodManager.get_codemod(name, start_path=state.parsed_codebase.repo_path)
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

        session = CodegenSession(state.parsed_codebase.repo_path)
        session.codebase = state.parsed_codebase

        # Capture output
        original_print = print
        import builtins

        builtins.print = capture_output

        try:
            # Run the codemod using run_local

            codemod.run(state.parsed_codebase)
            state.parsed_codebase.get_diff()
            logs = "\n".join(state.log_buffer)

            return {"message": f"Codemod '{name}' executed successfully", "logs": json.dumps(logs), "result": "Codemod applied successfully. Run `git diff` to view the changes!"}
        finally:
            # Restore original print
            builtins.print = original_print

    except Exception as e:
        return {"error": f"Error executing codemod: {str(e)}", "details": {"type": type(e).__name__, "message": str(e)}}


@mcp.tool(name="reset", description="Reset git repository while preserving all files in .codegen directory")
async def reset() -> Dict[str, Any]:
    try:
        # Import necessary functions from reset command
        from codegen.cli.commands.reset.main import backup_codegen_files, remove_untracked_files, restore_codegen_files
        from codegen.cli.git.repo import get_git_repo
        from pygit2.enums import ResetMode

        # Get the git repository
        repo = get_git_repo()
        if not repo:
            return {"error": "Not a git repository"}

        # Backup .codegen files and their staged status
        codegen_changes = backup_codegen_files(repo)

        # Reset everything
        repo.reset(repo.head.target, ResetMode.HARD)

        # Restore .codegen files and their staged status
        restore_codegen_files(repo, codegen_changes)

        # Remove untracked files except .codegen
        remove_untracked_files(repo)

        return {
            "message": "Reset complete. Repository has been restored to HEAD (preserving .codegen) and untracked files have been removed (except .codegen)",
            "preserved_files": len(codegen_changes),
        }
    except Exception as e:
        return {"error": f"Error during reset: {str(e)}"}


################################################################################
# CUSTOM TOOLS
################################################################################


@mcp.tool(name="reveal_symbol", description="Shows all usages + dependencies of the provided symbol, up to the specified max depth (e.g. show 2nd-level usages/dependencies)")
async def reveal_symbol_fn(
    symbol: Annotated[str, "symbol to show usages and dependencies for"],
    filepath: Annotated[str, "file path to the target file to split"] = None,
    max_depth: Annotated[int, "maximum depth to show dependencies"] = 1,
):
    codebase = state.parsed_codebase
    output = reveal_symbol(codebase=codebase, symbol_name=symbol, filepath=filepath, max_depth=max_depth, max_tokens=10000)
    return output


@mcp.tool(name="split_out_functions", description="split out the functions in defined in the provided file into new files, re-importing them to the original")
@requires_parsed_codebase
async def split_out_functions(target_file: Annotated[str, "file path to the target file to split"]):
    new_files = {}
    codebase = state.parsed_codebase
    file = codebase.get_file(target_file)
    # for each test_function in the file
    for function in file.functions:
        # Create a new file for each test function using its name
        new_file = codebase.create_file(f"{file.directory.path}/{function.name}.py", sync=False)
        # Move the test function to the newly created file
        function.move_to_file(new_file, strategy="add_back_edge")
        new_files[new_file.filepath] = [function.name]

    codebase.commit()
    result = {"description": "the following new files have been created with each with containing the function specified", "new_files": new_files}
    return json.dumps(result, indent=2)


################################################################################
# MAIN
################################################################################


def main():
    print("starting codegen-mcp-server")
    # Start parsing the codebase on server boot
    print("starting codebase parsing")
    state.parse(state.codebase_path)
    print("codebase parsing started")
    run = mcp.run_stdio_async()
    print("codegen-mcp-server started")
    asyncio.get_event_loop().run_until_complete(run)


if __name__ == "__main__":
    main()
