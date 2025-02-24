import uuid
import warnings

import rich_click as click
from langchain_core.messages import SystemMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

from codegen.extensions.langchain.agent import create_agent_with_tools
from codegen.extensions.langchain.tools import (
    CreateFileTool,
    DeleteFileTool,
    EditFileTool,
    ListDirectoryTool,
    MoveSymbolTool,
    RenameFileTool,
    RevealSymbolTool,
    SearchTool,
    ViewFileTool,
)
from codegen.sdk.core.codebase import Codebase

# Suppress specific warnings
warnings.filterwarnings("ignore", message=".*Helicone.*")
warnings.filterwarnings("ignore", message=".*LangSmith.*")
warnings.filterwarnings("ignore", category=DeprecationWarning)

console = Console()

WELCOME_ART = r"""[bold blue]
   ____          _
  / ___|___   __| | ___  __ _  ___ _ __
 | |   / _ \ / _` |/ _ \/ _` |/ _ \ '_ \
 | |__| (_) | (_| |  __/ (_| |  __/ | | |
  \____\___/ \__,_|\___|\__, |\___|_| |_|
                        |___/

[/bold blue]
"""


@click.command(name="agent")
@click.option("--query", "-q", default=None, help="Initial query for the agent.")
def agent_command(query: str):
    """Start an interactive chat session with the Codegen AI agent."""
    # Show welcome message
    console.print(WELCOME_ART)

    # Initialize codebase from current directory
    with console.status("[bold green]Initializing codebase...[/bold green]"):
        codebase = Codebase("./")

    # Helper function for agent to print messages
    def say(message: str):
        console.print()  # Add blank line before message
        markdown = Markdown(message)
        console.print(markdown)
        console.print()  # Add blank line after message

    # Initialize tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
        CreateFileTool(codebase),
        DeleteFileTool(codebase),
        RenameFileTool(codebase),
        MoveSymbolTool(codebase),
        RevealSymbolTool(codebase),
        EditFileTool(codebase),
        # RunBashCommandTool(codebase),
    ]

    # Initialize chat history with system message
    system_message = SystemMessage(
        content="""You are a helpful AI assistant with access to the local codebase.
You can help with code exploration, editing, and general programming tasks.
Always explain what you're planning to do before taking actions."""
    )

    # Get initial query if not provided via command line
    if not query:
        console.print("[bold]Welcome to the Codegen CLI Agent![/bold]")
        console.print("I'm an AI assistant that can help you explore and modify code in this repository.")
        console.print("I can help with tasks like viewing files, searching code, making edits, and more.")
        console.print()
        console.print("What would you like help with today?")
        console.print()
        query = Prompt.ask("[bold]>[/bold]")  # Simple arrow prompt

    # Create the agent
    agent = create_agent_with_tools(codebase=codebase, tools=tools, system_message=system_message)

    # Main chat loop
    while True:
        if not query:  # Only prompt for subsequent messages
            user_input = Prompt.ask("\n[bold]>[/bold]")  # Simple arrow prompt
        else:
            user_input = query
            query = None  # Clear the initial query so we enter the prompt flow

        if user_input.lower() in ["exit", "quit"]:
            break

        # Invoke the agent
        with console.status("[bold green]Agent is thinking...") as status:
            try:
                thread_id = str(uuid.uuid4())
                result = agent.invoke(
                    {"input": user_input},
                    config={"configurable": {"thread_id": thread_id}},
                )

                result = result["messages"][-1].content
                # Update chat history with AI's response
                if result:
                    say(result)
            except Exception as e:
                console.print(f"[bold red]Error during agent execution:[/bold red] {e}")
                break
