"""Agent command for creating remote agent runs."""

import json
from pathlib import Path

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
from codegen.git.repo_operator.local_git_repo import LocalGitRepo
from codegen.git.repo_operator.repo_operator import RepoOperator
from codegen.git.schemas.repo_config import RepoConfig

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


# For backward compatibility, also allow `codegen agent --prompt "..."`, `codegen agent --id X --json`, and `codegen agent --id X pull`
def agent(
    action: str = typer.Argument(None, help="Action to perform: 'pull' to checkout PR branch"),
    prompt: str | None = typer.Option(None, "--prompt", "-p", help="The prompt to send to the agent"),
    agent_id: int | None = typer.Option(None, "--id", help="Agent run ID to fetch or pull"),
    as_json: bool = typer.Option(False, "--json", help="Output raw JSON response"),
    org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)"),
    model: str | None = typer.Option(None, help="Model to use for this agent run (optional)"),
    repo_id: int | None = typer.Option(None, help="Repository ID to use for this agent run (optional)"),
):
    """Create a new agent run with the given prompt, fetch an existing agent run by ID, or pull PR branch."""
    if prompt:
        # If prompt is provided, create the agent run
        create(prompt=prompt, org_id=org_id, model=model, repo_id=repo_id)
    elif agent_id and action == "pull":
        # If agent ID and pull action provided, pull the PR branch
        pull(agent_id=agent_id, org_id=org_id)
    elif agent_id:
        # If agent ID is provided, fetch the agent run
        get(agent_id=agent_id, as_json=as_json, org_id=org_id)
    else:
        # If none of the above, show help
        console.print("[red]Error:[/red] Either --prompt or --id is required")
        console.print("Usage:")
        console.print("  [cyan]codegen agent --prompt 'Your prompt here'[/cyan]      # Create agent run")
        console.print("  [cyan]codegen agent --id 123 --json[/cyan]                   # Fetch agent run as JSON")
        console.print("  [cyan]codegen agent --id 123 pull[/cyan]                     # Pull PR branch")
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


@agent_app.command()
def pull(
    agent_id: int = typer.Option(..., "--id", help="Agent run ID to pull PR branch for"),
    org_id: int | None = typer.Option(None, help="Organization ID (defaults to CODEGEN_ORG_ID/REPOSITORY_ORG_ID or auto-detect)"),
):
    """Fetch and checkout the PR branch for an agent run."""
    token = get_current_token()
    if not token:
        console.print("[red]Error:[/red] Not authenticated. Please run 'codegen login' first.")
        raise typer.Exit(1)

    resolved_org_id = resolve_org_id(org_id)
    if resolved_org_id is None:
        console.print("[red]Error:[/red] Organization ID not provided. Pass --org-id, set CODEGEN_ORG_ID, or REPOSITORY_ORG_ID.")
        raise typer.Exit(1)

    # Check if we're in a git repository
    try:
        current_repo = LocalGitRepo(Path.cwd())
        if not current_repo.has_remote():
            console.print("[red]Error:[/red] Current directory is not a git repository with remotes.")
            raise typer.Exit(1)
    except Exception:
        console.print("[red]Error:[/red] Current directory is not a valid git repository.")
        raise typer.Exit(1)

    # Fetch agent run data
    spinner = create_spinner(f"Fetching agent run {agent_id}...")
    spinner.start()

    try:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{API_ENDPOINT.rstrip('/')}/v1/organizations/{resolved_org_id}/agent/run/{agent_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        agent_data = response.json()
    except requests.HTTPError as e:
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
    finally:
        spinner.stop()

    # Check if agent run has PRs
    github_prs = agent_data.get("github_pull_requests", [])
    if not github_prs:
        console.print(f"[yellow]Warning:[/yellow] Agent run {agent_id} has no associated pull requests.")
        raise typer.Exit(1)

    if len(github_prs) > 1:
        console.print(f"[yellow]Warning:[/yellow] Agent run {agent_id} has multiple PRs. Using the first one.")

    pr = github_prs[0]
    pr_url = pr.get("url")
    head_branch_name = pr.get("head_branch_name")

    if not pr_url:
        console.print("[red]Error:[/red] PR URL not found in agent run data.")
        raise typer.Exit(1)

    if not head_branch_name:
        # Try to extract branch name from PR URL as fallback
        # GitHub PR URLs often follow patterns like:
        # https://github.com/owner/repo/pull/123
        # We can use GitHub API to get the branch name
        console.print("[yellow]Info:[/yellow] HEAD branch name not in API response, attempting to fetch from GitHub...")
        try:
            # Extract owner, repo, and PR number from PR URL manually
            # Expected format: https://github.com/owner/repo/pull/123
            if not pr_url.startswith("https://github.com/"):
                msg = f"Only GitHub URLs are supported, got: {pr_url}"
                raise ValueError(msg)

            # Remove the GitHub base and split the path
            path_parts = pr_url.replace("https://github.com/", "").split("/")
            if len(path_parts) < 4 or path_parts[2] != "pull":
                msg = f"Invalid GitHub PR URL format: {pr_url}"
                raise ValueError(msg)

            owner = path_parts[0]
            repo = path_parts[1]
            pr_number = path_parts[3]

            # Use GitHub API to get PR details
            import requests as github_requests

            github_api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"

            github_response = github_requests.get(github_api_url)
            if github_response.status_code == 200:
                pr_data = github_response.json()
                head_branch_name = pr_data.get("head", {}).get("ref")
                if head_branch_name:
                    console.print(f"[green]✓ Found branch name from GitHub API:[/green] {head_branch_name}")
                else:
                    console.print("[red]Error:[/red] Could not extract branch name from GitHub API response.")
                    raise typer.Exit(1)
            else:
                console.print(f"[red]Error:[/red] Failed to fetch PR details from GitHub API (status: {github_response.status_code})")
                console.print("[yellow]Tip:[/yellow] The PR may be private or the GitHub API rate limit may be exceeded.")
                raise typer.Exit(1)
        except Exception as e:
            console.print(f"[red]Error:[/red] Could not fetch branch name from GitHub: {e}")
            console.print("[yellow]Tip:[/yellow] The backend may need to be updated to include branch information.")
            raise typer.Exit(1)

    # Parse PR URL to get repository information
    try:
        # Extract owner and repo from PR URL manually
        # Expected format: https://github.com/owner/repo/pull/123
        if not pr_url.startswith("https://github.com/"):
            msg = f"Only GitHub URLs are supported, got: {pr_url}"
            raise ValueError(msg)

        # Remove the GitHub base and split the path
        path_parts = pr_url.replace("https://github.com/", "").split("/")
        if len(path_parts) < 4 or path_parts[2] != "pull":
            msg = f"Invalid GitHub PR URL format: {pr_url}"
            raise ValueError(msg)

        owner = path_parts[0]
        repo = path_parts[1]
        pr_repo_full_name = f"{owner}/{repo}"
    except Exception as e:
        console.print(f"[red]Error:[/red] Could not parse PR URL: {pr_url} - {e}")
        raise typer.Exit(1)

    # Check if current repository matches PR repository
    current_repo_full_name = current_repo.full_name
    if not current_repo_full_name:
        console.print("[red]Error:[/red] Could not determine current repository name.")
        raise typer.Exit(1)

    if current_repo_full_name.lower() != pr_repo_full_name.lower():
        console.print("[red]Error:[/red] Repository mismatch!")
        console.print(f"  Current repo: [cyan]{current_repo_full_name}[/cyan]")
        console.print(f"  PR repo:      [cyan]{pr_repo_full_name}[/cyan]")
        console.print("[yellow]Tip:[/yellow] Navigate to the correct repository directory first.")
        raise typer.Exit(1)

    # Perform git operations with safety checks
    try:
        repo_config = RepoConfig.from_repo_path(str(Path.cwd()))
        repo_operator = RepoOperator(repo_config)

        # Safety check: warn if repository has uncommitted changes
        if repo_operator.git_cli.is_dirty():
            console.print("[yellow]⚠️  Warning:[/yellow] You have uncommitted changes in your repository.")
            console.print("These changes may be lost when switching branches.")

            # Get user confirmation
            confirm = typer.confirm("Do you want to continue? Your changes may be lost.")
            if not confirm:
                console.print("[yellow]Operation cancelled.[/yellow]")
                raise typer.Exit(0)

            console.print("[blue]Proceeding with branch checkout...[/blue]")

        console.print(f"[blue]Repository match confirmed:[/blue] {current_repo_full_name}")
        console.print(f"[blue]Fetching and checking out branch:[/blue] {head_branch_name}")

        # Fetch the branch from remote
        fetch_spinner = create_spinner("Fetching latest changes from remote...")
        fetch_spinner.start()
        try:
            fetch_result = repo_operator.fetch_remote("origin")
            if fetch_result.name != "SUCCESS":
                console.print(f"[yellow]Warning:[/yellow] Fetch result: {fetch_result.name}")
        except Exception as e:
            console.print(f"[red]Error during fetch:[/red] {e}")
            raise
        finally:
            fetch_spinner.stop()

        # Check if the branch already exists locally
        local_branches = [b.name for b in repo_operator.git_cli.branches]
        if head_branch_name in local_branches:
            console.print(f"[yellow]Info:[/yellow] Local branch '{head_branch_name}' already exists. It will be reset to match the remote.")

        # Checkout the remote branch
        checkout_spinner = create_spinner(f"Checking out branch {head_branch_name}...")
        checkout_spinner.start()
        try:
            checkout_result = repo_operator.checkout_remote_branch(head_branch_name)
            if checkout_result.name == "SUCCESS":
                console.print(f"[green]✓ Successfully checked out branch:[/green] {head_branch_name}")
            elif checkout_result.name == "NOT_FOUND":
                console.print(f"[red]Error:[/red] Branch {head_branch_name} not found on remote.")
                console.print("[yellow]Tip:[/yellow] The branch may have been deleted or renamed.")
                raise typer.Exit(1)
            else:
                console.print(f"[yellow]Warning:[/yellow] Checkout result: {checkout_result.name}")
        except Exception as e:
            console.print(f"[red]Error during checkout:[/red] {e}")
            raise
        finally:
            checkout_spinner.stop()

        # Display success info
        console.print(
            Panel(
                f"[green]✓ Successfully pulled PR branch![/green]\n\n"
                f"[cyan]Agent Run:[/cyan]    {agent_id}\n"
                f"[cyan]Repository:[/cyan]   {current_repo_full_name}\n"
                f"[cyan]Branch:[/cyan]       {head_branch_name}\n"
                f"[cyan]PR URL:[/cyan]       {pr_url}",
                title="🌿 [bold]Branch Checkout Complete[/bold]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2),
            )
        )

    except Exception as e:
        console.print(f"[red]Error during git operations:[/red] {e}")
        raise typer.Exit(1)
