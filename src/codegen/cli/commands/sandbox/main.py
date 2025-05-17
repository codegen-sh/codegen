import secrets

import rich_click as click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from codegen.cli.sandbox.sandbox import start_sandbox_server

console = Console()

DEFAULT_CALLBACK_URL = "http://localhost:8081/codegen_callback_results"

CODEGEN_ASCII_ART = """
 ██████╗ ██████╗ ██████╗ ███████╗███╗   ██╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗  ██║
██║     ██║   ██║██║  ██║█████╗  ██╔██╗ ██║
██║     ██║   ██║██████╔╝██╔══╝  ██║╚██╗██║
╚██████╗╚██████╔╝██╔ Scor╝███████╗██║ ╚████║
 ╚═════╝ ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝
"""


@click.command("sandbox")
@click.option("--port", default=8000, help="Port to run the local server on.", type=int, show_default=True)
@click.option("--auth-token", default=None, help="Authentication token. If not provided, a new one is generated.", type=str)
@click.option(
    "--callback-url",
    "callback_url_option",  # Use a different internal name to distinguish from the variable
    default=None,  # Will be handled to set DEFAULT_CALLBACK_URL if None
    help=f"URL to POST command results back to. Defaults to {DEFAULT_CALLBACK_URL} if not explicitly set to empty or another URL.",
    type=str,
)
@click.option("--disable-callback", is_flag=True, help="Explicitly disable the callback POST even if a default URL is set.")
def sandbox_command(port: int, auth_token: str | None, callback_url_option: str | None, disable_callback: bool):
    """Starts a local FastAPI server to act as a command execution sandbox.

    The server exposes an /execute endpoint (POST) that accepts a JSON body:
    {"command": "your shell command here"}

    If an --auth-token is provided, it must be sent in the X-Auth-Token header.
    If no token is provided, one will be generated and displayed.
    By default, command execution details will be POSTed to {DEFAULT_CALLBACK_URL}.
    Use --callback-url to specify a different URL, or --disable-callback to turn it off.
    """
    console.print(Panel(Text(CODEGEN_ASCII_ART, style="bold cyan"), title="[bold green]Codegen[/bold green] Sandbox Mode", expand=False))

    token_to_use = auth_token
    if not token_to_use:
        token_to_use = secrets.token_hex(16)
        console.print("[bold yellow]No --auth-token provided. Generated a new secure token:[/bold yellow]")
    else:
        console.print("[bold yellow]Using provided --auth-token:[/bold yellow]")

    console.print(Panel(Text(token_to_use, style="bold white on blue"), title="[bold green]Authentication Token (X-Auth-Token)[/bold green]", expand=False, padding=(1, 2)))
    if not auth_token:
        console.print("Include this token in the 'X-Auth-Token' header for all requests to the /execute endpoint.")

    actual_callback_url = DEFAULT_CALLBACK_URL
    using_default_callback_url = True

    if disable_callback:
        actual_callback_url = None
        using_default_callback_url = False  # Not using any callback URL
    elif callback_url_option is not None:
        actual_callback_url = callback_url_option if callback_url_option else None  # Allow explicit empty string to disable
        using_default_callback_url = False

    local_server_url = f"http://127.0.0.1:{port}"
    health_url = f"{local_server_url}/health"
    execute_url = f"{local_server_url}/execute"

    server_info_text = Text.assemble(
        ("Local Server URL: ", "bold green"),
        (local_server_url, "underline blue"),
        "\n",
        ("Health Check:     ", "bold green"),
        (health_url, "underline blue"),
        "\n",
        ("Execute Endpoint: ", "bold green"),
        (execute_url, "underline blue"),
        (" (POST)", "dim"),
    )

    if actual_callback_url:
        server_info_text.append("\n")
        callback_message_style = "bold magenta"
        if using_default_callback_url:
            server_info_text.append(Text.assemble(("Default Callback: ", callback_message_style), (actual_callback_url, "underline blue")))
            server_info_text.append(Text.assemble((" (Ensure a listener is active there)", "dim magenta")))
        else:
            server_info_text.append(Text.assemble(("Callback URL:     ", callback_message_style), (actual_callback_url, "underline blue")))
    elif not disable_callback and callback_url_option == "":  # Explicitly disabled with empty string
        server_info_text.append("\n")
        server_info_text.append(Text.assemble(("Callback POST:    ", "bold yellow"), ("Disabled (explicitly by empty --callback-url)", "yellow")))

    console.print(Panel(server_info_text, title="[bold green]Server Endpoints & Configuration[/bold green]", expand=False, padding=(1, 1)))

    if token_to_use:
        console.print("[cyan]Authentication is enabled (token will be checked by server).[/cyan]")
    else:
        console.print("[bold red]Warning: Authentication is DISABLED. The server is open.[/bold red]")

    console.print("\nStarting sandbox server process...")
    console.print("[dim]Press Ctrl+C to stop the server.[/dim]")
    start_sandbox_server(port=port, auth_token=token_to_use, callback_url=actual_callback_url)
    console.print("[bold green]Codegen Sandbox server has shut down.[/bold green]")


if __name__ == "__main__":
    sandbox_command()
