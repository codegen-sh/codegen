"""Agent command for creating remote agent runs."""

import json

import requests
import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from codegen.cli.api.endpoints import API_ENDPOINT
from codegen.cli.auth.token_manager import get_current_org_name, get_current_token
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.org import resolve_org_id

console = Console()

# Create the agent app
agent_app = typer.Typer(help="Create and manage individual agent runs")


@agent_app.command()
def create(
    prompt: str = typer.Option(..., "--prompt", "-p", help="The prompt to send to the agent"),
    org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)"),
    model: str | None = typer.Option(None, help="Model to use for this agent run (optional)"),
    repo_id: int | None = typer.Option(None, help="Repository ID to use for this agent run (optional)"),
):
    """Create a new agent run with the given prompt."""
    # Get the current token
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    try:
        # Resolve org id
        resolved_org_id = resolve_org_id(org_id)
        if resolved_org_id is None:
            console.print("[red]Error:[/red] Organization ID not provided. Pass --org-id, set CODEGEN_ORG_ID, or REPOSITORY_ORG_ID.")
            raise typer.Exit(1)

        # Prepare the request payload
        payload = {
            "prompt": prompt,
        }

        if model:
            payload["model"] = model
        if repo_id:
            payload["repo_id"] = repo_id

        # Make API request to create agent run with spinner
        spinner = create_spinner("Creating agent run...")
        spinner.start()

        try:
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/agent/run"
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            agent_run_data = response.json()
        finally:
            spinner.stop()

        # Extract agent run information
        run_id = agent_run_data.get("id", "Unknown")
        status = agent_run_data.get("status", "Unknown")
        web_url = agent_run_data.get("web_url", "")
        created_at = agent_run_data.get("created_at", "")

        # Format created date
        if created_at:
            try:
                from datetime import datetime

                dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                created_display = dt.strftime("%B %d, %Y at %H:%M")
            except (ValueError, TypeError):
                created_display = created_at
        else:
            created_display = "Unknown"

        # Status with emoji
        status_display = status
        if status == "COMPLETE":
            status_display = "✅ Complete"
        elif status == "RUNNING":
            status_display = "🏃 Running"
        elif status == "FAILED":
            status_display = "❌ Failed"
        elif status == "STOPPED":
            status_display = "⏹️ Stopped"
        elif status == "PENDING":
            status_display = "⏳ Pending"

        # Create result display
        result_info = []
        result_info.append(f"[cyan]Agent Run ID:[/cyan] {run_id}")
        result_info.append(f"[cyan]Status:[/cyan]       {status_display}")
        result_info.append(f"[cyan]Created:[/cyan]      {created_display}")
        if web_url:
            result_info.append(f"[cyan]Web URL:[/cyan]      {web_url}")

        result_text = "\n".join(result_info)

        console.print(
            Panel(
                result_text,
                title="🤖 [bold]Agent Run Created[/bold]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

        # Show next steps
        console.print("\n[dim]💡 Track progress with:[/dim] [cyan]codegen agents[/cyan]")
        if web_url:
            console.print(f"[dim]🌐 View in browser:[/dim]  [link]{web_url}[/link]")

    except requests.RequestException as e:
        console.print(f"[red]Error creating agent run:[/red] {e}", style="bold red")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_detail = e.response.json().get("detail", "Unknown error")
                console.print(f"[red]Details:[/red] {error_detail}")
            except (ValueError, KeyError):
                pass
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}", style="bold red")
        raise typer.Exit(1)


# Default callback for the agent app
@agent_app.callback(invoke_without_command=True)
def agent_callback(ctx: typer.Context):
    """Create and manage individual agent runs."""
    if ctx.invoked_subcommand is None:
        # If no subcommand is provided, show help
        print(ctx.get_help())
        raise typer.Exit()


# For backward compatibility, also allow `codegen agent --prompt "..."` and `codegen agent --id X --json`
def agent(
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="The prompt to send to the agent"),
    agent_id: int | None = typer.Option(None, "--id", help="Agent run ID to fetch"),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON response"),
    org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)"),
    model: str | None = typer.Option(None, help="Model to use for this agent run (optional)"),
    repo_id: int | None = typer.Option(None, help="Repository ID to use for this agent run (optional)"),
):
    """Create a new agent run with the given prompt, or fetch an existing agent run by ID."""
    if prompt:
        # If prompt is provided, create the agent run
        create(prompt=prompt, org_id=org_id, model=model, repo_id=repo_id)
    elif agent_id:
        # If agent ID is provided, fetch the agent run
        get(agent_id=agent_id, as_json=as_json, org_id=org_id)
    else:
        # If neither prompt nor agent_id, show help
        console.print("[red]Error:[/red] Either --prompt or --id is required")
        console.print("Usage:")
        console.print("  [cyan]codegen agent --prompt 'Your prompt here'[/cyan]      # Create agent run")
        console.print("  [cyan]codegen agent --id 123 --json[/cyan]                   # Fetch agent run as JSON")
        raise typer.Exit(1)


@agent_app.command()
def get(
    agent_id: int = typer.Option(..., "--id", help="Agent run ID to fetch"),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON response"),
    org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)"),
):
    """Fetch and display details for a specific agent run."""
    # Get the current token
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    try:
        # Resolve org id (fast, uses stored data)
        resolved_org_id = resolve_org_id(org_id)
        if resolved_org_id is None:
            console.print("[red]Error:[/red] Organization ID not provided. Pass --org-id, set CODEGEN_ORG_ID, or REPOSITORY_ORG_ID.")
            raise typer.Exit(1)

        spinner = create_spinner(f"Fetching agent run {agent_id}...")
        spinner.start()

        try:
            headers = {"Authorization": f"Bearer {token}"}
            # Fixed: Use /agent/run/{id} not /agent/runs/{id}
            url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/agent/run/{agent_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            agent_data = response.json()
        finally:
            spinner.stop()

        # Output the data
        if as_json:
            # Pretty print JSON with syntax highlighting
            formatted_json = json.dumps(agent_data, indent=2, sort_keys=True)
            syntax = Syntax(formatted_json, "json", theme="monokai", line_numbers=False)
            console.print(syntax)
        else:
            # Display formatted information (fallback for future enhancement)
            formatted_json = json.dumps(agent_data, indent=2, sort_keys=True)
            syntax = Syntax(formatted_json, "json", theme="monokai", line_numbers=False)
            console.print(syntax)

    except requests.HTTPError as e:
        # Get organization name for better error messages
        org_name = get_current_org_name()
        org_display = f"{org_name} ({resolved_org_id})" if org_name else f"organization {resolved_org_id}"

        if e.response.status_code == 404:
            console.print(f"[red]Error:[/red] Agent run {agent_id} not found in {org_display}.")
        elif e.response.status_code == 403:
            console.print(f"[red]Error:[/red] Access denied to agent run {agent_id} in {org_display}. Check your permissions.")
        else:
            console.print(f"[red]Error:[/red] HTTP {e.response.status_code}: {e}")
        raise typer.Exit(1)
    except requests.RequestException as e:
        console.print(f"[red]Error fetching agent run:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)
