import logging

from codegen import CodeAgent, CodegenApp
from codegen.extensions.github.types.events.pull_request import PullRequestLabeledEvent
from codegen.extensions.linear.types import LinearEvent
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

    # Codebase
    logger.info("[CODEBASE] Initializing codebase")
    codebase = app.get_codebase("fastapi/fastapi")

    # Code Agent
    logger.info("[CODE_AGENT] Initializing code agent")
    agent = CodeAgent(codebase=codebase)

    logger.info("[CODE_AGENT] Running code agent")
    response = agent.run(event.text)

    app.slack.client.chat_postMessage(channel=event.channel, text=response, thread_ts=event.ts)
    return {"message": "Mentioned", "received_text": event.text, "response": response}


@app.github.event("pull_request:labeled")
def handle_pr(event: PullRequestLabeledEvent):
    logger.info(f"PR labeled: {event}")
    codebase = app.get_codebase("fastapi/fastapi")
    return {"message": "PR event handled", "num_files": len(codebase.files), "num_functions": len(codebase.functions)}


@app.linear.event("Issue")
def handle_issue(event: LinearEvent):
    logger.info(f"Issue created: {event}")
    codebase = app.get_codebase("fastapi/fastapi")
    return {"message": "Linear Issue event", "num_files": len(codebase.files), "num_functions": len(codebase.functions)}


if __name__ == "__main__":
    # Run the server
    app.run(port=8000)
