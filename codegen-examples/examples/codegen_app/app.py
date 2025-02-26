import logging

import modal
from codegen import CodeAgent, CodegenApp
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.linear.types import LinearEvent
from codegen.extensions.slack.types import SlackEvent
from codegen.extensions.tools.github.create_pr_comment import create_pr_comment

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

########################################################################################################################
# EVENTS
########################################################################################################################

# Create the cg_app
cg = CodegenApp(name="codegen-test", repos=["codegen-sh/Kevin-s-Adventure-Game"])


@cg.slack.event("app_mention")
async def handle_mention(event: SlackEvent):
    logger.info("[APP_MENTION] Received cg_app_mention event")
    logger.info(event)

    # Codebase
    logger.info("[CODEBASE] Initializing codebase")
    codebase = cg.get_codebase("codegen-sh/Kevin-s-Adventure-Game")

    # Code Agent
    logger.info("[CODE_AGENT] Initializing code agent")
    agent = CodeAgent(codebase=codebase)

    logger.info("[CODE_AGENT] Running code agent")
    response = agent.run(event.text)

    cg.slack.client.chat_postMessage(channel=event.channel, text=response, thread_ts=event.ts)
    return {"message": "Mentioned", "received_text": event.text, "response": response}


@cg.github.event("pull_request:labeled")
def handle_pr(event: PullRequestLabeledEvent):
    logger.info("PR labeled")
    logger.info(f"PR head sha: {event.pull_request.head.sha}")
    codebase = cg.get_codebase("codegen-sh/Kevin-s-Adventure-Game")

    # =====[ Check out commit ]=====
    # Might require fetch?
    logger.info("> Checking out commit")
    codebase.checkout(commit=event.pull_request.head.sha)

    logger.info("> Getting files")
    file = codebase.get_file("README.md")

    # =====[ Create PR comment ]=====
    create_pr_comment(codebase, event.pull_request.number, f"File content:\n```python\n{file.content}\n```")

    return {"message": "PR event handled", "num_files": len(codebase.files), "num_functions": len(codebase.functions)}


@cg.linear.event("Issue")
def handle_issue(event: LinearEvent):
    logger.info(f"Issue created: {event}")
    codebase = cg.get_codebase("codegen-sh/Kevin-s-Adventure-Game")
    return {"message": "Linear Issue event", "num_files": len(codebase.files), "num_functions": len(codebase.functions)}


########################################################################################################################
# MODAL DEPLOYMENT
########################################################################################################################
# This deploys the FastAPI app to Modal
# TODO: link this up with memory snapshotting.

# For deploying local package
REPO_URL = "https://github.com/codegen-sh/codegen-sdk.git"
COMMIT_ID = "26dafad2c319968e14b90806d42c6c7aaa627bb0"

# Create the base image with dependencies
base_image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        # =====[ Codegen ]=====
        # "codegen",
        f"git+{REPO_URL}@{COMMIT_ID}",
        # =====[ Rest ]=====
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_sdk",
    )
)

app = modal.App("codegen-test")


@app.function(image=base_image, secrets=[modal.Secret.from_dotenv()])
@modal.asgi_app()
def fastapi_app():
    return cg.app
