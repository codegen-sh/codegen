"""CLI program for deep code research using Codegen."""

import sys
import warnings
from pathlib import Path
from typing import Optional

import rich_click as click
from codegen import Codebase
from codegen.extensions.langchain.agent import create_agent_with_tools
from codegen.extensions.langchain.tools import (
    ListDirectoryTool,
    RevealSymbolTool,
    SearchTool,
    SemanticSearchTool,
    ViewFileTool,
)
from langchain_core.messages import SystemMessage
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt

# Suppress LangSmith warning
warnings.filterwarnings("ignore", message="API key must be provided when using hosted LangSmith API")

# Add the project root to Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

# Configure rich-click
click.rich_click.USE_RICH_MARKUP = True
click.rich_click.USE_MARKDOWN = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "yellow italic"
click.rich_click.ERRORS_SUGGESTION = "Try running the command with --help for more information"

console = Console()

RESEARCH_AGENT_PROMPT = """You are a code research expert. Your goal is to help users understand codebases by:
1. Finding relevant code through semantic and text search
2. Analyzing symbol relationships and dependencies
3. Exploring directory structures
4. Reading and explaining code

Always explain your findings in detail and provide context about how different parts of the code relate to each other.
When analyzing code, consider:
- The purpose and functionality of each component
- How different parts interact
- Key patterns and design decisions
- Potential areas for improvement

Break down complex concepts into understandable pieces and use examples when helpful."""


def initialize_codebase(repo_name: str) -> Optional[Codebase]:
    """Initialize a codebase with a spinner showing progress."""
    with console.status("") as status:
        try:
            # Update status with specific steps
            status.update(f"[bold blue]Cloning {repo_name}...[/bold blue]")
            codebase = Codebase.from_repo(repo_name)
            status.update("[bold green]✓ Repository cloned successfully![/bold green]")
            return codebase
        except Exception as e:
            console.print(f"[bold red]Error initializing codebase:[/bold red] {e}")
            return None


@click.group()
def cli():
    """[bold blue]🔍 Codegen Code Research CLI[/bold blue]

    A powerful tool for deep code analysis and research.
    """
    pass


@cli.command()
@click.argument("repo_name", required=False)
@click.option("--query", "-q", default=None, help="Initial research query to start with.")
def research(repo_name: Optional[str] = None, query: Optional[str] = None):
    """[bold green]Start a code research session[/bold green]

    [blue]Arguments:[/blue]
        [yellow]REPO_NAME[/yellow]: GitHub repository in format 'owner/repo' (optional, will prompt if not provided)
    """
    # If no repo name provided, prompt for it
    if not repo_name:
        console.print("\n[bold]Welcome to the Code Research CLI![/bold]")
        console.print("\nEnter a GitHub repository to analyze (format: owner/repo)\nExamples:\n  • fastapi/fastapi\n  • pytorch/pytorch\n  • microsoft/TypeScript")
        repo_name = Prompt.ask("\n[bold cyan]Repository name[/bold cyan]")

    # Initialize codebase
    codebase = initialize_codebase(repo_name)
    if not codebase:
        return

    # Create research tools
    tools = [
        ViewFileTool(codebase),
        ListDirectoryTool(codebase),
        SearchTool(codebase),
        SemanticSearchTool(codebase),
        RevealSymbolTool(codebase),
    ]

    # Initialize agent with research tools
    with console.status("[bold blue]Initializing research agent...[/bold blue]") as status:
        agent = create_agent_with_tools(codebase=codebase, tools=tools, chat_history=[SystemMessage(content=RESEARCH_AGENT_PROMPT)], verbose=True)
        status.update("[bold green]✓ Research agent ready![/bold green]")

    # Get initial query if not provided
    if not query:
        console.print(
            "\n[bold]What would you like to research?[/bold]"
            "\n[dim]Example queries:[/dim]"
            "\n• [italic]Explain the main components and their relationships[/italic]"
            "\n• [italic]Find all usages of X function/class[/italic]"
            "\n• [italic]Show me the dependency graph for Y module[/italic]"
            "\n• [italic]What design patterns are used in this codebase?[/italic]"
        )
        query = Prompt.ask("\n[bold cyan]Research query[/bold cyan]")

    # Main research loop
    while True:
        if not query:
            query = Prompt.ask("\n[bold cyan]Research query[/bold cyan]")

        if query.lower() in ["exit", "quit"]:
            console.print("\n[bold green]Thanks for using the Code Research CLI! Goodbye![/bold green]")
            break

        # Run the agent
        with console.status("[bold blue]Researching...[/bold blue]", spinner="dots") as status:
            try:
                result = agent.invoke(
                    {"input": query},
                    config={"configurable": {"session_id": "research"}},
                )
                # Display the result
                console.print("\n[bold blue]📊 Research Findings:[/bold blue]")
                console.print(Markdown(result["output"]))
            except Exception as e:
                console.print(f"\n[bold red]Error during research:[/bold red] {e}")

        # Clear query for next iteration
        query = None


if __name__ == "__main__":
    cli()
