"""Slack chatbot for answering questions about FastAPI using Codegen's VectorIndex."""

import os
from typing import Any

import modal
from codegen import Codebase
from codegen.extensions import VectorIndex
from fastapi import FastAPI, Request
from openai import OpenAI
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

########################################################
# Core RAG logic
########################################################


def format_response(answer: str, context: list[tuple[str, int]]) -> str:
    """Format the response for Slack with file links."""
    response = f"*Answer:*\n{answer}\n\n*Relevant Files:*\n"
    for filename, score in context:
        github_link = f"https://github.com/codegen-sh/codegen-sdk/blob/develop/{filename}"
        response += f"• <{github_link}|{filename}>\n"
    return response


def answer_question(query: str) -> tuple[str, list[tuple[str, int]]]:
    """Use RAG to answer a question about FastAPI."""
    # Initialize codebase. Smart about caching.
    codebase = Codebase.from_repo("codegen-sh/codegen-sdk", language="python", tmp_dir="/root")

    # Initialize vector index
    index = VectorIndex(codebase)

    # Try to load existing index or create new one
    index_path = "/root/E.pkl"
    try:
        index.load(index_path)
    except FileNotFoundError:
        # Create new index if none exists
        index.create()
        index.save(index_path)

    # Find relevant files
    results = index.similarity_search(query, k=5)

    # Collect context from relevant files
    context = ""
    for filepath, score in results:
        if "#chunk" in filepath:
            filepath = filepath.split("#chunk")[0]
        file = codebase.get_file(filepath)
        context += f"File: {file.filepath}\n```\n{file.content}\n```\n\n"

    # Create prompt for OpenAI
    prompt = f"""You are an expert on FastAPI. Given the following code context and question, provide a clear and accurate answer.
Focus on the specific code shown in the context and FastAPI's implementation details.

Note that your response will be rendered in Slack, so make sure to use Slack markdown. Keep it short + sweet, like 2 paragraphs + some code blocks max.

Question: {query}

Relevant code:
{context}

Answer:"""

    client = OpenAI()
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a code expert. Answer questions about the given repo based on RAG'd results."},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    return response.choices[0].message.content, results


########################################################
# Modal + Slack Setup
########################################################

# Create image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        "slack-bolt>=1.18.0",
        "codegen>=0.6.1",
        "openai>=1.1.0",
    )
)

# Create Modal app
app = modal.App("codegen-slack-demo")


@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=3600,
)
@modal.asgi_app()
def fastapi_app():
    """Create FastAPI app with Slack handlers."""
    # Initialize Slack app with secrets from environment
    slack_app = App(
        token=os.environ["SLACK_BOT_TOKEN"],
        signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    )

    # Create FastAPI app
    web_app = FastAPI()
    handler = SlackRequestHandler(slack_app)

    # Store responded messages to avoid duplicates
    responded = {}

    @slack_app.event("app_mention")
    def handle_mention(event: dict[str, Any], say: Any) -> None:
        """Handle mentions of the bot in channels."""
        print("#####[ Received Event ]#####")
        print(event)

        # Skip if we've already answered this question
        # Seems like Slack likes to double-send events while debugging (?)
        if event["ts"] in responded:
            return
        responded[event["ts"]] = True

        # Get message text without the bot mention
        query = event["text"].split(">", 1)[1].strip()
        if not query:
            say("Please ask a question about FastAPI!")
            return

        try:
            # Add typing indicator emoji
            slack_app.client.reactions_add(
                channel=event["channel"],
                timestamp=event["ts"],
                name="writing_hand",
            )

            # Get answer using RAG
            answer, context = answer_question(query)

            # Format and send response in thread
            response = format_response(answer, context)
            say(text=response, thread_ts=event["ts"])

        except Exception as e:
            # Send error message in thread
            say(text=f"Error: {str(e)}", thread_ts=event["ts"])

    @web_app.post("/")
    async def endpoint(request: Request):
        """Handle Slack events and verify requests."""
        return await handler.handle(request)

    @web_app.post("/slack/verify")
    async def verify(request: Request):
        """Handle Slack URL verification challenge."""
        data = await request.json()
        if data["type"] == "url_verification":
            return {"challenge": data["challenge"]}
        return await handler.handle(request)

    return web_app
