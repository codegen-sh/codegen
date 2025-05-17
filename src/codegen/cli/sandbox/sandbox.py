import secrets
import subprocess
import threading
import time

import httpx  # For making HTTP requests for the callback
import rich
import uvicorn
from fastapi import BackgroundTasks, Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

DEFAULT_PORT = 8000
console = Console()  # For rich printing within the server logic

app = FastAPI()

# Globals to be configured by start_sandbox_server
SERVER_AUTH_TOKEN = None
CALLBACK_URL = None


# Request model for the execute endpoint
class CommandRequest(BaseModel):
    command: str
    # We can add more fields later, like arguments, working directory, etc.


# Dependency to check for the auth token
async def verify_token(x_auth_token: str = Header(None)):
    if SERVER_AUTH_TOKEN:
        if not x_auth_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated: X-Auth-Token header missing",
            )
        if x_auth_token != SERVER_AUTH_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authentication credentials",
            )
    # If SERVER_AUTH_TOKEN is None, authentication is disabled
    return True  # Token is valid or auth is disabled


async def post_callback(command_details: dict):
    if CALLBACK_URL:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(CALLBACK_URL, json=command_details, timeout=10.0)  # 10s timeout
                response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
                console.print(Panel(Text(f"Successfully POSTed results to {CALLBACK_URL}. Status: {response.status_code}", style="green"), title="[Callback Success]"))
        except httpx.RequestError as e:
            console.print(Panel(Text(f"Error POSTing to callback URL {CALLBACK_URL}: {e!s}", style="bold red"), title="[Callback Request Error]"))
        except httpx.HTTPStatusError as e:
            console.print(Panel(Text(f"Callback URL {CALLBACK_URL} returned error status {e.response.status_code}: {e.response.text}", style="bold red"), title="[Callback HTTP Error]"))
        except Exception as e:
            console.print(Panel(Text(f"An unexpected error occurred during callback to {CALLBACK_URL}: {e!s}", style="bold red"), title="[Callback Unexpected Error]"))


@app.get("/health", dependencies=[Depends(verify_token)])
async def health_check():
    return {"status": "ok", "authenticated": bool(SERVER_AUTH_TOKEN)}


@app.post("/execute", dependencies=[Depends(verify_token)])
async def execute_command(request: CommandRequest, background_tasks: BackgroundTasks):
    """Executes a shell command and returns its output."""
    command_to_run = request.command

    # Aesthetic local printing of the command being run
    console.print(Panel(Text.assemble(("Received command: ", "cyan"), (command_to_run, "white bold")), title="[bold blue]Incoming Command[/bold blue]", expand=False, border_style="blue"))

    try:
        rich.print(f"Executing command: {command_to_run}")
        # Using shell=True can be a security risk if the command string is
        # constructed from external input not properly sanitized.
        # For this controlled environment, it might be acceptable, but be cautious.
        process = subprocess.run(
            command_to_run,
            shell=True,
            capture_output=True,
            text=True,
            check=False,  # Don't raise an exception for non-zero exit codes
        )
        rich.print(f"Command stdout: {process.stdout}")
        if process.stderr:
            rich.print(f"[yellow]Command stderr:[/yellow] {process.stderr}")

        result_for_callback = {
            "command": command_to_run,
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "returncode": process.returncode,
        }

        # Combine stdout and stderr for local display
        final_stdout = process.stdout.strip()
        final_stderr = process.stderr.strip()

        output_display_string = ""
        if final_stdout:
            output_display_string += final_stdout
        if final_stderr:
            if output_display_string:  # If there was stdout, add a newline before stderr
                output_display_string += "\n"
            output_display_string += final_stderr

        if not output_display_string:  # If both were empty (or just whitespace after strip)
            output_display_string = "<no output>"

        console.print(Panel(Text(output_display_string), title="[bold blue]Command Output[/bold blue]", border_style="blue", expand=False))

        status_style = "green" if process.returncode == 0 else "red"
        status_panel = Panel(Text(str(process.returncode), style=f"bold {status_style}"), title=f"[bold {status_style}]Return Code[/bold {status_style}]", border_style=status_style, expand=False)
        console.print(status_panel)

        if CALLBACK_URL:
            background_tasks.add_task(post_callback, result_for_callback)

        return result_for_callback
    except Exception as e:
        console.print(Panel(Text(f"Error executing command '{command_to_run}': {e!s}", style="bold red"), title="[Execution Error]"))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def start_sandbox_server(port: int = DEFAULT_PORT, auth_token: str | None = None, callback_url: str | None = None):
    """Starts the local FastAPI server, sets up authentication and callback URL."""
    global SERVER_AUTH_TOKEN, CALLBACK_URL
    SERVER_AUTH_TOKEN = auth_token
    CALLBACK_URL = callback_url

    if SERVER_AUTH_TOKEN:
        console.print(Panel(f"Authentication: [bold green]Enabled[/bold green]. Expecting X-Auth-Token: {SERVER_AUTH_TOKEN}", title="[Server Auth Status]"))
    else:
        console.print(Panel("Authentication: [bold red]Disabled[/bold red]. Server is open.", title="[Server Auth Status]"))

    if CALLBACK_URL:
        console.print(Panel(f"Callback POST: [bold green]Enabled[/bold green]. Results will be sent to: {CALLBACK_URL}", title="[Server Callback Status]"))
    else:
        console.print(Panel("Callback POST: [bold yellow]Disabled[/bold yellow].", title="[Server Callback Status]"))

    # Start FastAPI server in a separate thread
    server_thread = threading.Thread(target=uvicorn.run, args=(app,), kwargs={"host": "127.0.0.1", "port": port, "log_level": "warning"})
    server_thread.daemon = True
    server_thread.start()

    # Server details will be printed by the calling command for better aesthetics

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        # Message moved to the command function for cleaner exit
        pass  # Let finally block handle shutdown
    finally:
        console.print("\n[cyan]Shutting down FastAPI server...[/cyan]")
        # Uvicorn server running in a daemon thread will exit when the main thread exits
        console.print("[green]FastAPI server stopped.[/green]")


if __name__ == "__main__":
    # Example usage
    generated_token = secrets.token_hex(16)
    example_callback = "http://localhost:9999/results"  # Example, won't work unless something listens here
    rich.print(f"Starting server with token: {generated_token} and callback to {example_callback}")
    start_sandbox_server(auth_token=generated_token, callback_url=example_callback)
