import os
import subprocess
from pathlib import Path

import rich_click as click

from codegen.cli.auth.session import CodegenSession
from codegen.cli.rich.spinners import create_spinner
from codegen.cli.utils.notebooks import create_notebook
from codegen.cli.workspace.decorators import requires_init
from codegen.cli.workspace.venv_manager import VenvManager


def create_jupyter_dir(codegen_dir: Path) -> Path:
    """Create and return the jupyter directory."""
    jupyter_dir = codegen_dir / "jupyter"
    jupyter_dir.mkdir(parents=True, exist_ok=True)
    return jupyter_dir


@click.command(name="notebook")
@click.option("--background", is_flag=True, help="Run Jupyter Lab in the background")
@click.option("--demo", is_flag=True, help="Create a demo notebook with FastAPI example code")
@requires_init
def notebook_command(session: CodegenSession, background: bool, demo: bool):
    """Launch Jupyter Lab with a pre-configured notebook for exploring your codebase."""
    with create_spinner("Setting up Jupyter environment...") as status:
        venv = VenvManager(codegen_dir=session.codegen_dir)

        status.update("Checking Jupyter installation...")
        venv.ensure_jupyter()

        jupyter_dir = create_jupyter_dir(session.codegen_dir)
        notebook_path = create_notebook(jupyter_dir, demo=demo)

        status.update("Running Jupyter Lab...")

        # Prepare the environment with the virtual environment activated
        env = {**os.environ, "VIRTUAL_ENV": str(venv.venv_dir), "PATH": f"{venv.venv_dir}/bin:{os.environ['PATH']}"}

        # Run Jupyter Lab
        subprocess.run(["jupyter", "lab", str(notebook_path)], env=env, check=True)
