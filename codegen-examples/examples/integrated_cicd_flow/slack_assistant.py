"""Slack Assistant component for the integrated CI/CD flow.

This component provides assistance and notifications via Slack.
"""

import logging
import os
from typing import Any, Dict

import modal
from codegen import Codebase
from codegen.extensions.events.codegen_app import CodegenApp
from codegen.extensions.tools.semantic_search import semantic_search
from codegen.shared.enums.programming_language import ProgrammingLanguage
from fastapi import FastAPI, Request
from openai import OpenAI
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Modal image
image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install(
    "fastapi[standard]",
    "codegen>=0.22.2",
    "slack_bolt>=1.18.0",
    "openai>=1.1.0",
)

# Create Modal app
app = modal.App("slack-assistant")

# Default repository to analyze
DEFAULT_REPO = "codegen-sh/codegen-sdk"


def format_response(answer: str, context: list[tuple[str, float]]) -> str:
    """Format the response for Slack with file links.
    
    Args:
        answer: The answer to the question
        context: The context used to generate the answer
        
    Returns:
        A formatted response for Slack
    """
    response = f"*Answer:*\n{answer}\n\n*Relevant Files:*\n"
    for filepath, score in context:
        github_link = f"https://github.com/codegen-sh/codegen-sdk/blob/develop/{filepath}"
        response += f"• <{github_link}|{filepath}>\n"
    return response


def answer_question(query: str, codebase: Codebase) -> tuple[str, list[tuple[str, float]]]:
    """Use RAG to answer a question about the codebase.
    
    Args:
        query: The question to answer
        codebase: The codebase to search
        
    Returns:
        A tuple of (answer, context)
    """
    # Find relevant files
    results = semantic_search(codebase, query, k=5)
    
    # Collect context from relevant files
    context = ""
    for filepath, score in results:
        file = codebase.get_file(filepath)
        context += f"File: {filepath}\n```\n{file.content}\n```\n\n"
    
    # Create prompt for OpenAI
    prompt = f"""You are an expert on the codebase. Given the following code context and question, provide a clear and accurate answer.
Focus on the specific code shown in the context and implementation details.

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


@app.function(
    image=image,
    secrets=[modal.Secret.from_dotenv()],
    timeout=3600,
)
@modal.asgi_app()
def fastapi_app():
    """Create FastAPI app with Slack handlers."""
    # Initialize codebase
    codebase = Codebase.from_repo(DEFAULT_REPO, language="python", tmp_dir="/root")
    
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
    def handle_mention(event: Dict[str, Any], say: Any) -> None:
        """Handle mentions of the bot in channels."""
        logger.info("Received app mention event")
        
        # Skip if we've already answered this question
        if event["ts"] in responded:
            return
        responded[event["ts"]] = True
        
        # Get message text without the bot mention
        query = event["text"].split(">", 1)[1].strip()
        if not query:
            say("Please ask a question about the codebase!")
            return
        
        try:
            # Add typing indicator emoji
            slack_app.client.reactions_add(
                channel=event["channel"],
                timestamp=event["ts"],
                name="writing_hand",
            )
            
            # Get answer using RAG
            answer, context = answer_question(query, codebase)
            
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


if __name__ == "__main__":
    # For local development
    modal.runner.deploy_stub("slack-assistant")