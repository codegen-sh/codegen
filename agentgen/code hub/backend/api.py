from fastapi import FastAPI
from pydantic import BaseModel
import modal
from codegen import Codebase
from codegen.extensions.langchain.agent import create_agent_with_tools
from codegen.extensions.langchain.tools import (
    ListDirectoryTool,
    RevealSymbolTool,
    SearchTool,
    SemanticSearchTool,
    ViewFileTool,
)
from langchain_core.messages import SystemMessage
from fastapi.middleware.cors import CORSMiddleware
from codegen.extensions.index.file_index import FileIndex
import os
from typing import List
from fastapi.responses import StreamingResponse
import json

image = (
    modal.Image.debian_slim()
    .apt_install("git")
    .pip_install(
        "codegen==0.22.1",
        "fastapi",
        "uvicorn",
        "langchain",
        "langchain-core",
        "pydantic",
    )
)

app = modal.App(
    name="code-research-app",
    image=image,
    secrets=[modal.Secret.from_name("agent-secret")],
)

fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Research agent prompt
RESEARCH_AGENT_PROMPT = """You are a code research expert. Your goal is to help users understand codebases by:
1. Finding relevant code through semantic and text search
2. Analyzing symbol relationships and dependencies
3. Exploring directory structures
4. Reading and explaining code

Always explain your findings in detail and provide context about how different parts of the code relate to each other.
When analyzing code, consider:
- The purpose and functionality of each component
- How different parts interact
- Key patterns and design decisions
- Potential areas for improvement

Break down complex concepts into understandable pieces and use examples when helpful."""

current_status = "Intializing process..."


def update_status(new_status: str):
    global current_status
    current_status = new_status
    return {"type": "status", "content": new_status}


class ResearchRequest(BaseModel):
    repo_name: str
    query: str


class ResearchResponse(BaseModel):
    response: str


class FilesResponse(BaseModel):
    files: List[str]


class StatusResponse(BaseModel):
    status: str


# @fastapi_app.post("/files", response_model=ResearchResponse)
# async def files(request: ResearchRequest) -> ResearchResponse:
#     codebase = Codebase.from_repo(request.repo_name)

#     file_index = FileIndex(codebase)
#     file_index.create()

#     similar_files = file_index.similarity_search(request.query, k=5)

#     similar_file_names = [file.filepath for file, score in similar_files]
#     return FilesResponse(files=similar_file_names)


@fastapi_app.post("/research", response_model=ResearchResponse)
async def research(request: ResearchRequest) -> ResearchResponse:
    """
    Endpoint to perform code research on a GitHub repository.
    """
    try:
        update_status("Initializing codebase...")
        codebase = Codebase.from_repo(request.repo_name)

        update_status("Creating research tools...")
        tools = [
            ViewFileTool(codebase),
            ListDirectoryTool(codebase),
            SearchTool(codebase),
            SemanticSearchTool(codebase),
            RevealSymbolTool(codebase),
        ]

        update_status("Initializing research agent...")
        agent = create_agent_with_tools(
            codebase=codebase,
            tools=tools,
            chat_history=[SystemMessage(content=RESEARCH_AGENT_PROMPT)],
            verbose=True,
        )

        update_status("Running analysis...")
        result = agent.invoke(
            {"input": request.query},
            config={"configurable": {"session_id": "research"}},
        )

        update_status("Complete")
        return ResearchResponse(response=result["output"])

    except Exception as e:
        update_status("Error occurred")
        return ResearchResponse(response=f"Error during research: {str(e)}")


@fastapi_app.post("/similar-files", response_model=FilesResponse)
async def similar_files(request: ResearchRequest) -> FilesResponse:
    """
    Endpoint to find similar files in a GitHub repository based on a query.
    """
    try:
        codebase = Codebase.from_repo(request.repo_name)
        file_index = FileIndex(codebase)
        file_index.create()
        similar_files = file_index.similarity_search(request.query, k=5)
        similar_file_names = [file.filepath for file, score in similar_files]
        return FilesResponse(files=similar_file_names)

    except Exception as e:
        update_status("Error occurred")
        return FilesResponse(files=[f"Error finding similar files: {str(e)}"])


@app.function()
async def get_similar_files(repo_name: str, query: str) -> List[str]:
    """
    Separate Modal function to find similar files
    """
    codebase = Codebase.from_repo(repo_name)
    file_index = FileIndex(codebase)
    file_index.create()
    similar_files = file_index.similarity_search(query, k=6)
    return [file.filepath for file, score in similar_files if score > 0.2]


@fastapi_app.post("/research/stream")
async def research_stream(request: ResearchRequest):
    """
    Streaming endpoint to perform code research on a GitHub repository.
    """
    try:

        async def event_generator():
            final_response = ""

            similar_files_future = get_similar_files.remote.aio(
                request.repo_name, request.query
            )

            codebase = Codebase.from_repo(request.repo_name)
            tools = [
                ViewFileTool(codebase),
                ListDirectoryTool(codebase),
                SearchTool(codebase),
                SemanticSearchTool(codebase),
                RevealSymbolTool(codebase),
            ]

            agent = create_agent_with_tools(
                codebase=codebase,
                tools=tools,
                chat_history=[SystemMessage(content=RESEARCH_AGENT_PROMPT)],
                verbose=True,
            )

            research_task = agent.astream_events(
                {"input": request.query},
                version="v1",
                config={"configurable": {"session_id": "research"}},
            )

            similar_files = await similar_files_future
            yield f"data: {json.dumps({'type': 'similar_files', 'content': similar_files})}\n\n"

            async for event in research_task:
                kind = event["event"]
                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        final_response += content
                        yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                elif kind in ["on_tool_start", "on_tool_end"]:
                    yield f"data: {json.dumps({'type': kind, 'data': event['data']})}\n\n"

            yield f"data: {json.dumps({'type': 'complete', 'content': final_response})}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
        )

    except Exception as e:
        error_status = update_status("Error occurred")
        return StreamingResponse(
            iter(
                [
                    f"data: {json.dumps(error_status)}\n\n",
                    f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n",
                ]
            ),
            media_type="text/event-stream",
        )


@app.function(image=image, secrets=[modal.Secret.from_name("agent-secret")])
@modal.asgi_app()
def fastapi_modal_app():
    return fastapi_app


if __name__ == "__main__":
    app.deploy("code-research-app")
