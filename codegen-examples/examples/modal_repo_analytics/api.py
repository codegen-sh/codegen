"""Modal API endpoint for repository analysis."""

import modal  # deptry: ignore
from codegen import Codebase
from pydantic import BaseModel

# Create image with dependencies
image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("fastapi[standard]", "codegen>=0.5.30")

# Create Modal app
app = modal.App("codegen-repo-analyzer")


class RepoMetrics(BaseModel):
    """Response model for repository metrics."""

    num_files: int = 0
    num_functions: int = 0
    num_classes: int = 0
    status: str = "success"
    error: str = ""


@app.function(image=image)
@modal.web_endpoint(method="GET")
def analyze_repo(repo_name: str) -> RepoMetrics:
    """Analyze a GitHub repository and return metrics.

    Args:
        repo_name: Repository name in format 'owner/repo'

    Returns:
        RepoMetrics object containing repository metrics or error information
    """
    try:
        # Validate input
        if "/" not in repo_name:
            return RepoMetrics(status="error", error="Repository name must be in format 'owner/repo'")

        # Initialize codebase
        codebase = Codebase.from_repo(repo_name)

        # Calculate metrics
        num_files = len(codebase.files(extensions="*"))  # Get all files
        num_functions = len(codebase.functions)
        num_classes = len(codebase.classes)

        return RepoMetrics(
            num_files=num_files,
            num_functions=num_functions,
            num_classes=num_classes,
        )

    except Exception as e:
        return RepoMetrics(status="error", error=str(e))
