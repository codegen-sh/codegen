import logging

from slack_sdk import WebClient

from codegen.extensions.events.codegen_app import CodegenApp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the app
app = CodegenApp(name="codegen-test")


@app.slack.event("app_mention")
def handle_mention(client: WebClient, event):
    logger.info("[APP_MENTION] Received app_mention event")

    # Example response
    client.chat_postMessage(channel=event.channel, text=f"Hello! You mentioned me in {event.channel}", thread_ts=event.ts)

    return {"message": "Event handled successfully"}


@app.github.event("pull_request:opened")
def handle_pr(event):
    logger.info(f"New PR opened: {event}")
    return {"message": "PR event handled"}


if __name__ == "__main__":
    # Run the server
    app.run(port=8000)
