import logging

from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.slack.types import SlackEvent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the app
app = CodegenApp(name="codegen-test", repos=["fastapi/fastapi"])


@app.slack.event("app_mention")
async def handle_mention(event: SlackEvent):
    logger.info("[APP_MENTION] Received app_mention event")
    logger.info(event)
    codebase = app.get_codebase("fastapi/fastapi")
    # Can access Slack client via app.slack.client if needed
    return {"num_files": len(codebase.files), "num_functions": len(codebase.functions)}


@app.github.event("pull_request:labeled")
def handle_pr(event: PullRequestLabeledEvent):
    logger.info(f"PR labeled: {event}")
    codebase = app.get_codebase("fastapi/fastapi")
    return {"message": "PR event handled", "num_files": len(codebase.files), "num_functions": len(codebase.functions)}


if __name__ == "__main__":
    # Run the server
    app.run(port=8000)
