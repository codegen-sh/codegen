# Codegen Deep Research

A code research tool that enables users to understand codebases through agentic AI analysis. The project combines a Modal-based FastAPI backend with a Next.js frontend to provide intelligent code exploration capabilities.

Users submit a GitHub repository and research query through the frontend. The Modal API processes the request using an AI agent equipped with specialized code analysis tools. The agent explores the codebase using various tools (search, symbol analysis, etc.) and results are returned to the frontend for display.

## How it Works

### Backend (Modal API)

The backend is built using [Modal](https://modal.com/) and [FastAPI](https://fastapi.tiangolo.com/), providing a serverless API endpoint for code research.

There is a main API endpoint that handles code research requests. It uses the `codegen` library for codebase analysis.

The agent investigates the codebase through various research tools:
- `ViewFileTool`: Read file contents
- `ListDirectoryTool`: Explore directory structures
- `SearchTool`: Text-based code search
- `SemanticSearchTool`: AI-powered semantic code search
- `RevealSymbolTool`: Analyze code symbols and relationships

```python
tools = [
    ViewFileTool(codebase),
    ListDirectoryTool(codebase),
    SearchTool(codebase),
    SemanticSearchTool(codebase),
    RevealSymbolTool(codebase)
]

# Initialize agent with research tools
agent = create_agent_with_tools(
    codebase=codebase,
    tools=tools,
    chat_history=[SystemMessage(content=RESEARCH_AGENT_PROMPT)],
    verbose=True
)
```

### Frontend (Next.js)

The frontend provides an interface for users to submit a GitHub repository and research query. The components come from the [shadcn/ui](https://ui.shadcn.com/) library. This triggers the Modal API to perform the code research and returns the results to the frontend.

## Getting Started

1. Set up environment variables in an `.env` file:
   ```
   OPENAI_API_KEY=your_key_here
   ```

2. Deploy or serve the Modal API:
   ```bash
   modal serve backend/api.py
   ```
   `modal serve` runs the API locally for development, creating a temporary endpoint that's active only while the command is running.
   ```bash
   modal deploy backend/api.py
   ```
   `modal deploy` creates a persistent Modal app and deploys the FastAPI app to it, generating a permanent API endpoint.
   
   After deployment, you'll need to update the API endpoint in the frontend configuration to point to your deployed Modal app URL.

3. Run the Next.js frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

## Learn More

More information about the `codegen` library can be found [here](https://codegen.com/).

For details on the agent implementation, check out [Deep Code Research with AI](https://docs.codegen.com/tutorials/deep-code-research) from the Codegen docs. This tutorial provides an in-depth guide on how the research agent is created.