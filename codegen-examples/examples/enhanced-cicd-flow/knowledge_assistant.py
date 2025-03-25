"""Knowledge Assistant for the enhanced CI/CD flow.

This component:
1. Provides context and assistance throughout the pipeline
2. Answers questions about the codebase and development process
3. Facilitates team communication and knowledge sharing
"""

import os
import logging
from typing import Dict, Any, Optional

import modal
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from shared import (
    BASE_IMAGE,
    create_app,
    create_codebase,
    logger,
)
from codegen.extensions import VectorIndex
from openai import OpenAI

# Create app
app = modal.App("knowledge-assistant")

# AI prompts for knowledge assistance
KNOWLEDGE_PROMPT = """
You are an expert software developer and knowledge assistant. Your task is to answer the following question about the codebase:

Question: {question}

Context:
{context}

Please provide a clear, concise answer based on the context provided. If you don't know the answer, say so and suggest where the user might find more information.
"""

@app.function(
    image=BASE_IMAGE,
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
    
    # Initialize codebase and vector index
    codebase = None
    index = None
    
    def get_codebase():
        """Get or initialize the codebase."""
        nonlocal codebase
        if codebase is None:
            codebase = create_codebase("codegen-sh/codegen", "python")
        return codebase
    
    def get_index():
        """Get or initialize the vector index."""
        nonlocal index, codebase
        if index is None:
            codebase = get_codebase()
            index = VectorIndex(codebase)
            
            # Try to load existing index or create new one
            index_path = "/root/codegen_index.pkl"
            try:
                index.load(index_path)
            except FileNotFoundError:
                # Create new index if none exists
                index.create()
                index.save(index_path)
        
        return index
    
    def format_response(answer: str, context: list[tuple[str, int]]) -> str:
        """Format the response for Slack with file links."""
        response = f"*Answer:*\n{answer}\n\n*Relevant Files:*\n"
        for filename, score in context:
            if "#chunk" in filename:
                filename = filename.split("#chunk")[0]
            github_link = f"https://github.com/codegen-sh/codegen/blob/develop/{filename}"
            response += f"• <{github_link}|{filename}>\n"
        return response
    
    def answer_question(query: str) -> tuple[str, list[tuple[str, int]]]:
        """Use RAG to answer a question about the codebase."""
        # Get vector index
        index = get_index()
        codebase = get_codebase()
        
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
        prompt = f"""You are an expert on the codegen codebase. Given the following code context and question, provide a clear and accurate answer.
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
    
    @slack_app.event("app_mention")
    def handle_mention(event: Dict[str, Any], say: Any) -> None:
        """Handle mentions of the bot in channels."""
        logger.info(f"Received Slack mention: {event}")
        
        # Skip if we've already answered this question
        if event["ts"] in responded:
            return
        responded[event["ts"]] = True
        
        # Get message text without the bot mention
        query = event["text"].split(">", 1)[1].strip()
        if not query:
            say("Please ask a question about the codebase or development process!")
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
    
    @web_app.post("/slack/events")
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