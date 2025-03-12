"""Modal API endpoint for RAG-based code Q&A using Codegen's VectorIndex."""

import modal
from codegen import Codebase
from codegen.extensions import VectorIndex
from pydantic import BaseModel

# Create image with dependencies
image = (
    modal.Image.debian_slim(python_version="3.13")
    .apt_install("git")
    .pip_install(
        "fastapi[standard]",
        "codegen>=0.5.30",
        "openai>=1.1.0",
    )
)

# Create Modal app
app = modal.App("codegen-rag-qa")

# Create stub for persistent volume to store vector indices
stub = modal.Stub("codegen-rag-qa")
volume = modal.Volume.from_name("codegen-indices")


class QARequest(BaseModel):
    """Request model for code Q&A."""

    repo_name: str
    query: str


class QAResponse(BaseModel):
    """Response model for code Q&A."""

    answer: str = ""
    context: list[dict[str, str]] = []  # List of {filepath, snippet} used for answer
    status: str = "success"
    error: str = ""


@stub.function(
    image=image,
    volumes={"/root/.codegen/indices": volume},
    timeout=600,
)
@modal.web_endpoint(method="POST")
async def answer_code_question(request: QARequest) -> QAResponse:
    """Answer questions about code using RAG with Codegen's VectorIndex.

    Args:
        request: QARequest containing repository name and query

    Returns:
        QAResponse containing answer and context snippets
    """
    try:
        # Validate input
        if "/" not in request.repo_name:
            return QAResponse(status="error", error="Repository name must be in format 'owner/repo'")

        # Initialize codebase
        codebase = Codebase.from_repo(request.repo_name)

        # Initialize vector index
        index = VectorIndex(codebase)

        # Try to load existing index or create new one
        try:
            index.load(f"/root/.codegen/indices/{request.repo_name.replace('/', '_')}.pkl")
        except FileNotFoundError:
            # Create new index if none exists
            index.create()
            index.save(f"/root/.codegen/indices/{request.repo_name.replace('/', '_')}.pkl")

        # Find relevant files
        results = index.similarity_search(request.query, k=3)

        # Collect context from relevant files
        context = []
        for filepath, score in results:
            try:
                file = codebase.get_file(filepath)
                if file:
                    context.append(
                        {
                            "filepath": filepath,
                            "snippet": file.content[:1000],  # First 1000 chars as preview
                            "score": f"{score:.3f}",
                        }
                    )
            except Exception as e:
                print(f"Error reading file {filepath}: {e}")

        # Format context for prompt
        context_str = "\n\n".join([f"File: {c['filepath']}\nScore: {c['score']}\n```\n{c['snippet']}\n```" for c in context])

        # Create prompt for OpenAI
        prompt = f"""Given the following code context and question, provide a clear and accurate answer.
Focus on the specific code shown in the context.

Question: {request.query}

Relevant code context:
{context_str}

Answer:"""

        # Get answer from OpenAI
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a helpful code assistant. Answer questions about code accurately and concisely based on the provided context."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        return QAResponse(answer=response.choices[0].message.content, context=[{"filepath": c["filepath"], "snippet": c["snippet"]} for c in context])

    except Exception as e:
        return QAResponse(status="error", error=str(e))
