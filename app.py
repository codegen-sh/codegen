from codegen.extensions.events.codegen_app import CodegenApp

# Create the app instance
app = CodegenApp(name="webhook-events")

# You can add custom event handlers here if needed
# For example:
# @app.on_slack_event("app_mention")
# async def handle_app_mention(event):
#     return {"text": "Hello! I received your mention."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app.app, host="127.0.0.1", port=8000) 