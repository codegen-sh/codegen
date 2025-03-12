import modal.running_app
from codegen.extensions.events.app import CodegenApp
import modal

image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("fastapi[standard]", "codegen>=v0.22.2")
app = CodegenApp(name="test-linear", modal_api_key="", image=image)

# Here is an example implementation of setting up an endpoint for receiving webhook events from Linear.
# The @app.linear.event() decorator takes care of subscribing to the webhook and also unsubscribing when the deployment spun
# Load environment variables from .env file


@app.cls(secrets=[modal.Secret.from_dotenv()], keep_warm=1)
class LinearEventHandlers:
    @modal.enter()
    def enter(self):
        app.linear.subscribe_all_handlers()

    @modal.exit()
    def exit(self):
        app.linear.unsubscribe_all_handlers()

    @modal.web_endpoint(method="POST")
    @app.linear.event("Issue")
    def test(self, data: dict):
        # handle webhook event
        # data is the payload of the webhook event
        print(data)
