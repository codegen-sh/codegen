# Repository Analyzer API

A simple Modal API endpoint that analyzes GitHub repositories using Codegen. The API returns basic metrics about any public GitHub repository including:

- Total number of files
- Number of functions
- Number of classes

## Running Locally

1. Install dependencies:

```bash
uv add modal
```

2. Start the API server:

```bash
modal serve src/codegen/extensions/modal/api.py
```

3. Test with curl:

```bash
# Replace with your local Modal endpoint URL
curl "{URL}?repo_name=fastapi/fastapi"
```

## Response Format

The API returns JSON in this format:

```json
{
  "status": "success",
  "error": "",
  "num_files": 123,
  "num_functions": 456,
  "num_classes": 78
}
```

If there's an error, you'll get:

```json
{
  "status": "error",
  "error": "Error message here",
  "num_files": 0,
  "num_functions": 0,
  "num_classes": 0
}
```

## Development

The API is built using:

- Modal for serverless deployment
- FastAPI for the web endpoint
- Codegen for repository analysis

To deploy changes:

```bash
modal deploy src/codegen/extensions/modal/api.py
```
