from codegen.extensions.swebench.utils import SweBenchExample
from codegen.extensions.swebench.harness import run_agent_on_entry
from codegen.git.schemas.repo_config import RepoConfig
from codegen.runner.clients.sandbox_client import RemoteSandboxClient
import modal
import sys
from modal import Dict
from modal import Sandbox, SandboxSnapshot
import time

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install("fastapi[standard]")
    .copy_local_dir("../../../", "/root/codegen", ignore=[".venv", "**/.venv", "tests", "**/tests"])
    .run_commands("pip install -e /root/codegen")
)

app = modal.App(name="swebench-agent-run", image=image, secrets=[modal.Secret.from_dotenv()])

# Dict to store codebase snapshots where the key is the repo full name <> commit hash
codebase_snapshots = Dict.from_name("codebase-snapshots", create_if_missing=True)


@app.function(timeout=5 * 60)
async def run_agent_modal(entry: SweBenchExample):
    """Modal function to process a single example from the SWE-bench dataset."""
    return run_agent_on_entry(entry)


@app.cls(image=image, secrets=[modal.Secret.from_dotenv()])
class SwebenchAgentRun:
    repo_full_name: str = modal.parameter()
    commit: str = modal.parameter()
    codebase_client: RemoteSandboxClient | None = None

    @modal.enter(snap=True)
    def load(self):
        repo_config = RepoConfig(self.repo_full_name, self.commit, "python")
        snapshot_id = self.repo_full_name + self.commit
        if codebase_snapshots.contains(snapshot_id):
            snapshot = SandboxSnapshot.from_id(snapshot_id)
            sb = Sandbox._experimental_from_snapshot(snapshot)
            self.codebase_client = RemoteSandboxClient.from_sandbox(sb)
        else:
            self.codebase_client = RemoteSandboxClient(repo_config)
            duration = 0
            while not self.codebase_client.healthcheck():
                time.sleep(1)
                duration += 1
                if duration > 60 * 10:
                    raise Exception("Codebase client failed to start within 10 minutes")

            snapshot = self.codebase_client.sandbox._experimental_snapshot()
            codebase_snapshots.put(snapshot_id, snapshot.object_id)

    @modal.exit()
    def exit(self):
        sys.exit(0)

    @modal.method()
    async def run(self, entry: SweBenchExample):
        return run_agent_on_entry(entry, codebase_client=self.codebase_client)


def _take_snapshot(sandbox: Sandbox) -> str | None:
    try:
        snapshot = sandbox._experimental_snapshot()
        return snapshot.object_id
    except Exception:
        return None
