from codegen.extensions.langchain.utils import SweBenchExample
from codegen.extensions.swebench.harness import process_one_instance
import modal

image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install("fastapi[standard]")
    .copy_local_dir("../../../", "/root/codegen", ignore=[".venv", "**/.venv", "tests", "**/tests"])
    .run_commands("pip install -e /root/codegen")
)
app = modal.App(name="swebench-agent-run", image=image, secrets=[modal.Secret.from_dotenv()])

# Here is an example implementation of setting up an endpoint for receiving webhook events from Linear.
# The @app.linear.event() decorator takes care of subscribing to the webhook and also unsubscribing when the deployment spun
# Load environment variables from .env file


@app.function(timeout=5 * 60)
async def process_entry(entry: SweBenchExample):
    return process_one_instance(entry)
