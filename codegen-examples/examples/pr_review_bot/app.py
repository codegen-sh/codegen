import logging
from logging import getLogger
import modal
from codegen.extensions.events.app import CodegenApp
from fastapi import Request
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent, PullRequestUnlabeledEvent
from helpers import remove_bot_comments, pr_review_agent

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

REPO_URL = "https://github.com/codegen-sh/codegen-sdk.git"
COMMIT_ID = "20ba52b263ba8bab552b5fb6f68ca3667c0309fb"

base_image = (
    modal.Image.debian_slim(python_version="3.12")
    .apt_install("git")
    .pip_install(
        # =====[ Codegen ]=====
        # "codegen>=0.18",
        f"git+{REPO_URL}@{COMMIT_ID}",
        # =====[ Rest ]=====
        "openai>=1.1.0",
        "fastapi[standard]",
        "slack_sdk",
    )
)

app = CodegenApp(name="github", image=base_image, modal_api_key="")


@app.github.event("pull_request:labeled")
def handle_labeled(event: PullRequestLabeledEvent):
    logger.info("[PULL_REQUEST:LABELED] Received pull request labeled event")
    logger.info(f"PR #{event.number} labeled with: {event.label.name}")
    logger.info(f"PR title: {event.pull_request.title}")
    # app.slack.client.chat_postMessage(
    #     channel="C08DPPSL1CG",
    #     text=f"PR #{event.number} labeled with: {event.label.name}",
    # )
    if event.label.name == "Codegen":
        app.slack.client.chat_postMessage(
            channel="C08DPPSL1CG",
            text=f"PR #{event.number} labeled with: {event.label.name}, waking up CodegenBot and starting review",
        )

        logger.info(f"PR ID: {event.pull_request.id}")
        logger.info(f"PR title: {event.pull_request.title}")
        logger.info(f"pr number: {event.number}, ")
        pr_review_agent(event)


@app.github.event("pull_request:unlabeled")
def handle_unlabeled(event: PullRequestUnlabeledEvent):
    logger.info("unlabeled")
    logger.info(event.action)
    logger.info(event.label.name)
    if event.label.name == "Codegen":
        remove_bot_comments(event)


@app.function(secrets=[modal.Secret.from_dotenv()])
@modal.web_endpoint(method="POST")
def entrypoint(event: dict, request: Request):
    logger.info("[OUTER] Received GitHub webhook")
    return app.github.handle(event, request)
