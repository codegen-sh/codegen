import uuid
import warnings

import rich_click as click
from langchain_core.messages import SystemMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

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

# List of suggested starting prompts
SUGGESTED_PROMPTS = [
    "What repositories can you see?",
    "Show me the structure of this codebase",
    "Find all files containing the function 'create_agent'",
    "What capabilities do you have?",
    "Help me understand the architecture of this project",
    "Show me the main entry points of this application",
]


@click.command(name="agent")
@click.option("--query", "-q", default=None, help="Initial query for the agent.")
@click.option("--help-prompts", is_flag=True, help="Show suggested prompts and exit.")
def agent_command(query: str, help_prompts: bool):
    """Start an interactive chat session with the Codegen AI agent."""
    # Show welcome message
    console.print(WELCOME_ART)

    # If help-prompts flag is set, show suggested prompts and exit
    if help_prompts:
        console.print("[bold]Suggested Starting Prompts:[/bold]")
        for i, prompt in enumerate(SUGGESTED_PROMPTS, 1):
            console.print(f"  {i}. [cyan]{prompt}[/cyan]")
        return

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

        # Display suggested prompts in a panel
        prompt_text = Text()
        prompt_text.append("Try asking me:\n", style="bold")
        for i, prompt in enumerate(SUGGESTED_PROMPTS[:3], 1):  # Show only first 3 suggestions
            prompt_text.append(f"{i}. ", style="bold cyan")
            prompt_text.append(f"{prompt}\n", style="cyan")
        prompt_text.append("\nOr type 'help' to see more suggested prompts", style="dim")

        console.print(Panel(prompt_text, title="Suggested Prompts", border_style="blue"))
        console.print()

        console.print("What would you like help with today?")
        console.print()
        query = Prompt.ask("[bold]>[/bold]")  # Simple arrow prompt

        # Handle 'help' command to show more suggested prompts
        if query.lower() in ["help", "--help", "man", "?", "examples"]:
            console.print("[bold]Suggested Starting Prompts:[/bold]")
            for i, prompt in enumerate(SUGGESTED_PROMPTS, 1):
                console.print(f"  {i}. [cyan]{prompt}[/cyan]")
            console.print()
            query = Prompt.ask("[bold]>[/bold]")  # Ask again after showing help

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

        # Handle 'help' command to show suggested prompts
        if user_input.lower() in ["help", "--help", "man", "?", "examples"]:
            console.print("[bold]Suggested Starting Prompts:[/bold]")
            for i, prompt in enumerate(SUGGESTED_PROMPTS, 1):
                console.print(f"  {i}. [cyan]{prompt}[/cyan]")
            continue

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
