from codegen import Codebase
from codegen.extensions.attribution.main import (
    add_attribution_to_symbols,
    analyze_ai_impact,
)
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import modal

image = modal.Image.debian_slim().apt_install("git").pip_install("codegen", "fastapi", "intervaltree", "pygit2", "requests")

app = modal.App(name="ai-impact-analysis", image=image)

fastapi_app = FastAPI()

fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@fastapi_app.post("/analyze")
async def analyze(repo_full_name: str):
    codebase = Codebase.from_repo(repo_full_name=repo_full_name, language="python", full_history=True)

    print("🤖 Analyzing AI impact on codebase...")

    ai_authors = [
        "renovate[bot]",
        "dependabot[bot]",
        "github-actions[bot]",
        "devin-ai-integration[bot]",
    ]

    results = analyze_ai_impact(codebase, ai_authors)

    print("\n🏷️ Adding attribution information to symbols...")
    add_attribution_to_symbols(codebase, ai_authors)
    print("✅ Attribution information added to symbols")

    return results


@app.function(image=image)
@modal.asgi_app()
def fastapi_modal_app():
    return fastapi_app


if __name__ == "__main__":
    app.deploy("ai-impact-analysis")
