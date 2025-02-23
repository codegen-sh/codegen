import logging

import modal

from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.slack.types import SlackEvent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Modal image with dependencies
image = modal.Image.debian_slim().pip_install(
    "fastapi[standard]",
    "uvicorn",
    "slack_sdk",
    "pydantic",
    "rich",
    "httpx",
)

# Create Modal app
app = modal.App(name="codegen-app", image=image)

# Create CodegenApp instance
cg_app = CodegenApp(name="codegen-test", repos=["fastapi/fastapi"])


@cg_app.slack.event("app_mention")
async def handle_mention(event: SlackEvent):
    logger.info("[APP_MENTION] Received app_mention event")
    logger.info(event)
    codebase = cg_app.get_codebase("fastapi/fastapi")
    return {"num_files": len(codebase.files), "num_functions": len(codebase.functions)}


@cg_app.github.event("pull_request:labeled")
def handle_pr(event: PullRequestLabeledEvent):
    logger.info(f"PR labeled: {event}")
    codebase = cg_app.get_codebase("fastapi/fastapi")
    return {"message": "PR event handled", "num_files": len(codebase.files), "num_functions": len(codebase.functions)}


# Create Modal ASGI app
@app.function(secrets=[modal.Secret.from_dotenv()], image=image)
@modal.asgi_app()
def fastapi_app():
    # Return the FastAPI app
    return app.app
