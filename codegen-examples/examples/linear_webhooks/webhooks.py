import modal.running_app
from codegen.extensions.events.app import CodegenApp
import modal

image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("fastapi[standard]", "codegen>=0.22.1")

app = CodegenApp(name="test-linear", modal_api_key="", image=image)

# Here is an example implementation of setting up an endpoint for receiving webhook events from Linear.
# The @app.linear.event() decorator takes care of subscribing to the webhook and also unsubscribing when the deployment spun


@app.cls(secrets=[modal.Secret.from_dotenv()])
class LinearEventHandlers:
    @modal.enter()
    def enter(self):
        pass

    @modal.exit()
    def exit(self):
        # unsubscribe all handlers
        app.linear.unsubscribe_all_handlers()

    @modal.web_endpoint(method="POST")
    @app.linear.event("Issue")
    def test(self, data: dict):
        # handle webhook event
        # data is the payload of the webhook event
        print(data)
