import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from uvicorn.config import Config
from uvicorn.server import Server

from codegen.extensions.events.client import CodegenClient
from codegen.extensions.events.codegen_app import CodegenApp

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def run_codegen_app():
    """Run the CodegenApp server as a context manager"""
    # Create the app
    app = CodegenApp(name="test-app")

    # Configure uvicorn
    config = Config(app=app.app, host="127.0.0.1", port=8000, log_level="info")
    server = Server(config=config)

    # Start the server
    server_task = asyncio.create_task(server.serve())
    await asyncio.sleep(1)  # Give the server a moment to start

    try:
        yield server
    finally:
        # Shutdown the server
        server.should_exit = True
        await server_task


async def test_slack_events():
    """Test sending various Slack events to the CodegenApp"""
    async with run_codegen_app():
        # Create a test client
        client = CodegenClient()

        try:
            # Test sending a simple message
            logger.info("Sending test message...")
            response = await client.send_slack_message(text="Hello codegen!", channel="C123TEST", event_type="message")
            logger.info(f"Response from simple message: {response}")

            # Test sending an app mention
            logger.info("Sending test app mention...")
            response = await client.send_slack_message(text="<@U123BOT> help me with this code", channel="C123TEST", event_type="app_mention")
            logger.info(f"Response from app mention: {response}")

        finally:
            client.close()


if __name__ == "__main__":
    try:
        asyncio.run(test_slack_events())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(0)
