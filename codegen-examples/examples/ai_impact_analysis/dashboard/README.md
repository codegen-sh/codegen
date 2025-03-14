# AI Impact Analysis Dashboard

A web dashboard for visualizing AI-generated code contributions in your codebase. This dashboard provides detailed insights about AI vs human contributions, helping understand the role of AI in a codebase development process.

## Setup

### Backend

1. Install dependencies:

```bash
uv venv
source .venv/bin/activate
uv pip install modal codegen fastapi
```

2. Deploy or serve the Modal endpoint:

```bash
modal serve backend/api.py
```

```bash
modal deploy backend/api.py
```

### Frontend

1. Install dependencies:

```bash
cd frontend
npm install
```

2. Update the API endpoint:
   Edit the fetch URL on line 29 in `components/repo-analysis-dashboard.tsx` to point to your Modal endpoint:

```bash
 fetch(`[your-modal-deployment-url]/analyze?repo_full_name=${repoFullName}`, {
    method: 'POST',
    })
```

3. Start the development server:

```bash
npm run dev
```

## Usage

1. Visit the dashboard in your browser (default: http://localhost:3000)
1. Enter a GitHub repository name (format: username/repo)
1. Click "Analyze Repo" to generate insights

The dashboard will display:

- Summary statistics of AI contributions
- Monthly contribution timeline
- Top files with AI contributions
- High-impact AI-authored symbols
- Contributor breakdown visualization

## Architecture

- **Backend**: Modal-deployed FastAPI service that:

  - Clones and analyzes repositories
  - Processes git history
  - Calculates AI impact metrics
  - Returns structured analysis data

- **Frontend**: Next.js application with:

  - Interactive charts
  - Visualized AI impact metrics

## Learn More

- [AI Impact Analysis Documentation](https://docs.codegen.com/tutorials/attributions)
- [Codegen Documentation](https://docs.codegen.com)

## Contributing

Feel free to submit issues and enhancement requests!
