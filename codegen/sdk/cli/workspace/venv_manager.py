import os
import subprocess
from pathlib import Path


class VenvManager:
    """Manages the virtual environment for codegen."""

    def __init__(self, codegen_dir: Path):
        self.codegen_dir = codegen_dir
        self.venv_dir = self.codegen_dir / ".venv"

    def is_initialized(self) -> bool:
        """Check if virtual environment exists."""
        python_path = self.venv_dir / "bin" / "python"
        return self.venv_dir.exists() and python_path.exists()

    def create_venv(self, python_version: str = "3.13"):
        """Create a virtual environment using uv."""
        self.codegen_dir.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["uv", "venv", "--python", python_version, str(self.venv_dir)],
            check=True,
        )

    def install_packages(self, *packages: str):
        """Install packages into the virtual environment using uv pip."""
        subprocess.run(
            ["uv", "pip", "install", *packages],
            check=True,
            env={**os.environ, "VIRTUAL_ENV": str(self.venv_dir)},
        )

    def run_python(self, script: str, *args: str):
        """Run a Python script in the virtual environment."""
        python_path = self.venv_dir / "bin" / "python"
        subprocess.run([str(python_path), "-c", script, *args], check=True)

    def get_activate_command(self) -> str:
        """Get the command to activate the virtual environment."""
        return f"source {self.venv_dir}/bin/activate"

    def is_active(self) -> bool:
        """Check if a virtual environment is active."""
        return "VIRTUAL_ENV" in os.environ

    def ensure_jupyter(self):
        """Ensure Jupyter Lab is installed in the virtual environment."""
        try:
            subprocess.run(
                [str(self.venv_dir / "bin" / "jupyter"), "--version"],
                check=True,
                capture_output=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.install_packages("jupyterlab")
