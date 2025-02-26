from codegen.extensions.swebench.utils import SweBenchExample
from codegen.extensions.swebench.harness import run_agent_on_entry
import modal
import sys
from codegen.sdk.core.codebase import Codebase

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install(["git", "ripgrep"])
    .pip_install("fastapi[standard]")
    .copy_local_dir("../../../", "/root/codegen", ignore=[".venv", "**/.venv", "tests", "**/tests"])
    .run_commands("pip install -e /root/codegen")
)

app = modal.App(name="swebench-agent-run", image=image, secrets=[modal.Secret.from_dotenv()])


@app.function(timeout=5 * 60)
async def run_agent_modal(entry: SweBenchExample):
    """Modal function to process a single example from the SWE-bench dataset."""
    return run_agent_on_entry(entry)


@app.cls(image=image, secrets=[modal.Secret.from_dotenv()], enable_memory_snapshot=True)
class SwebenchAgentRun:
    repo_full_name: str = modal.parameter()
    commit: str = modal.parameter()
    codebase: Codebase | None = None

    @modal.enter(snap=True)
    def load(self):
        self.codebase = Codebase.from_repo(repo_full_name=self.repo_full_name, commit=self.commit, language="python")

    @modal.exit()
    def exit(self):
        sys.exit(0)

    @modal.method()
    async def run(self, entry: SweBenchExample):
        return run_agent_on_entry(entry, codebase=self.codebase)
