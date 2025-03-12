# Codegen RAG Q&A API

<p align="center">
  <a href="https://docs.codegen.com">
    <img src="https://i.imgur.com/6RF9W0z.jpeg" />
  </a>
</p>

<h2 align="center">
  Answer questions about any GitHub repository using RAG
</h2>

<div align="center">

[![Documentation](https://img.shields.io/badge/Docs-docs.codegen.com-purple?style=flat-square)](https://docs.codegen.com)
[![License](https://img.shields.io/badge/Code%20License-Apache%202.0-gray?&color=gray)](https://github.com/codegen-sh/codegen-sdk/tree/develop?tab=Apache-2.0-1-ov-file)

</div>

This example demonstrates how to build a RAG-powered code Q&A API using Codegen's VectorIndex and Modal. The API can answer questions about any GitHub repository by:

1. Creating embeddings for all files in the repository
1. Finding the most relevant files for a given question
1. Using GPT-4 to generate an answer based on the context

## Quick Start

1. Install dependencies:

```bash
pip install modal-client codegen openai
```

2. Create a Modal volume for storing indices:

```bash
modal volume create codegen-indices
```

3. Start the API server:

```bash
modal serve api.py
```

4. Test with curl:

```bash
curl -X POST "http://localhost:8000/answer_code_question" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "fastapi/fastapi",
    "query": "How does FastAPI handle dependency injection?"
  }'
```

## API Reference

### POST /answer_code_question

Request body:

```json
{
  "repo_name": "owner/repo",
  "query": "Your question about the code"
}
```

Response format:

```json
{
  "status": "success",
  "error": "",
  "answer": "Detailed answer based on the code...",
  "context": [
    {
      "filepath": "path/to/file.py",
      "snippet": "Relevant code snippet..."
    }
  ]
}
```

## How It Works

1. The API uses Codegen to clone and analyze the repository
1. It creates/loads a VectorIndex of all files using OpenAI's embeddings
1. For each question:
   - Finds the most semantically similar files
   - Extracts relevant code snippets
   - Uses GPT-4 to generate an answer based on the context

## Development

The API is built using:

- Modal for serverless deployment
- Codegen for repository analysis
- OpenAI for embeddings and Q&A
- FastAPI for the web endpoint

To deploy changes:

```bash
modal deploy api.py
```

## Environment Variables

Required environment variables:

- `OPENAI_API_KEY`: Your OpenAI API key

## Learn More

- [Codegen Documentation](https://docs.codegen.com)
- [Modal Documentation](https://modal.com/docs)
- [VectorIndex Tutorial](https://docs.codegen.com/building-with-codegen/semantic-code-search)
