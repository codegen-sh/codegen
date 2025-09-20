from contextlib import nullcontext
from pathlib import Path

from rich.status import Status

from codegen.sdk.cli.auth.constants import CODEGEN_DIR, DOCS_DIR, EXAMPLES_DIR, PROMPTS_DIR
from codegen.sdk.cli.auth.session import CliSession
from codegen.sdk.cli.rich.spinners import create_spinner
from codegen.sdk.cli.utils.notebooks import create_notebook
from codegen.sdk.cli.workspace.venv_manager import VenvManager


def initialize_codegen(session: CliSession, status: Status | str = "Initializing") -> CliSession:
    """Initialize or update the codegen directory structure and content.

    Args:
        status: Either a Status object to update, or a string action being performed ("Initializing" or "Updating")
        session: Optional CliSession for fetching docs and examples
        fetch_docs: Whether to fetch docs and examples (requires auth)

    Returns:
        Tuple of (codegen_folder, docs_folder, examples_folder)
    """
    CODEGEN_FOLDER = session.repo_path / CODEGEN_DIR
    PROMPTS_FOLDER = session.repo_path / PROMPTS_DIR
    DOCS_FOLDER = session.repo_path / DOCS_DIR
    EXAMPLES_FOLDER = session.repo_path / EXAMPLES_DIR
    JUPYTER_DIR = CODEGEN_FOLDER / "jupyter"
    CODEMODS_DIR = CODEGEN_FOLDER / "codemods"

    # If status is a string, create a new spinner
    context = create_spinner(f"   {status} folders...") if isinstance(status, str) else nullcontext()

    with context as spinner:
        status_obj = spinner if isinstance(status, str) else status

        # Create folders if they don't exist
        CODEGEN_FOLDER.mkdir(parents=True, exist_ok=True)
        PROMPTS_FOLDER.mkdir(parents=True, exist_ok=True)
        JUPYTER_DIR.mkdir(parents=True, exist_ok=True)
        CODEMODS_DIR.mkdir(parents=True, exist_ok=True)

        # Initialize virtual environment
        status_obj.update(f"   {'Creating' if isinstance(status, str) else 'Checking'} virtual environment...")
        venv = VenvManager(session.codegen_dir)
        if not venv.is_initialized():
            venv.create_venv()
            venv.install_packages("codegen")

        status_obj.update(f"   {'Updating' if isinstance(status, Status) else status} .gitignore...")
        modify_gitignore(CODEGEN_FOLDER)

        # Create notebook template
        create_notebook(JUPYTER_DIR)

    return CODEGEN_FOLDER, DOCS_FOLDER, EXAMPLES_FOLDER


def add_to_gitignore_if_not_present(gitignore: Path, line: str):
    if not gitignore.exists():
        gitignore.write_text(line)
    elif line not in gitignore.read_text():
        gitignore.write_text(gitignore.read_text() + "\n" + line)


def modify_gitignore(codegen_folder: Path):
    """Update .gitignore to track only specific Graph-sitter files."""
    gitignore_path = codegen_folder / ".gitignore"

    # Define what should be ignored (everything except codemods)
    ignore_patterns = [
        "# Codegen",
        "docs/",
        "examples/",
        "prompts/",
        "jupyter/",
        ".venv/",  # Add venv to gitignore
        "codegen-system-prompt.txt",
        "",
        "# Python cache files",
        "**/__pycache__/",
        "*.py[cod]",
        "*$py.class",
        "*.txt",
        "*.pyc",
        "",
    ]

    # Write or update .gitignore
    if not gitignore_path.exists():
        gitignore_path.write_text("\n".join(ignore_patterns) + "\n")
    else:
        # Read existing content
        content = gitignore_path.read_text()

        # Check if our section already exists
        if "# Codegen" not in content:
            # Add a newline if the file doesn't end with one
            if content and not content.endswith("\n"):
                content += "\n"
            # Add our patterns
            content += "\n" + "\n".join(ignore_patterns) + "\n"
            gitignore_path.write_text(content)
