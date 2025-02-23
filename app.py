import logging

from slack_sdk import WebClient

from codegen.extensions.events.codegen_app import CodegenApp

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the app
app = CodegenApp(name="codegen-test", repos=["fastapi/fastapi"])


@app.slack.event("app_mention")
async def handle_mention(client: WebClient, event):
    logger.info("[APP_MENTION] Received app_mention event")
    codebase = app.get_codebase("fastapi/fastapi")
    return {"num_files": len(codebase.files)}


@app.github.event("pull_request:opened")
def handle_pr(event):
    logger.info(f"New PR opened: {event}")
    return {"message": "PR event handled"}


if __name__ == "__main__":
    # Run the server
    app.run(port=8000)
