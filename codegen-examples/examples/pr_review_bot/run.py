import json

import codegen
from codegen import Codebase
from codegen.sdk.codebase.config import CodebaseConfig
from codegen.sdk.secrets import Secrets
from codegen.shared.configs.models.feature_flags import CodebaseFeatureFlags

github_token = "Your github token"
open_ai_key = "your open ai key"
pr_number = 0  # Your PR number must be an integer

codegen.function("pr-review-bot")


def run(codebase: Codebase):
    context_symbols = set()

    modified_symbols = codebase.get_modified_symbols_in_pr(pr_number)
    for symbol in modified_symbols:
        # Get direct dependencies
        deps = symbol.dependencies(max_depth=2)
        context_symbols.update(deps)

    # Prepare context for LLM
    context = {
        "modified_symbols": [
            {
                "name": symbol.name,
                "type": symbol.symbol_type.value,
                "filepath": symbol.filepath,
                "content": symbol.content,
            }
            for symbol in modified_symbols
        ],
        "context_symbols": [
            {
                "name": symbol.name,
                "type": symbol.symbol_type.value,
                "filepath": symbol.filepath,
                "content": symbol.content,
            }
            for symbol in context_symbols
        ],
    }

    system_prompt = """
    You are a helpful assistant that reviews pull requests and provides feedback on the code.
    """
    # Generate review using AI
    prompt = f"""Please review this pull request based on the following context:

Title: {context["pr_title"]}
Description: {context["pr_body"]}

Modified Symbols:
{json.dumps(context["modified_symbols"], indent=2)}

Related Context (Dependencies):
{json.dumps(context["context_symbols"], indent=2)}

Please provide a thorough code review that includes:
1. Overall assessment
2. Specific feedback on modified code
3. Potential issues or improvements
4. Impact on dependencies
5. Suggestions for testing
"""

    review = codebase.ai_client.llm_query_with_retry(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": prompt}], model="gpt-4", max_tokens=2000, temperature=0.7)
    return review


if __name__ == "__main__":
    print("Starting codebase analysis...")
    codebase = Codebase.from_repo(
        "getsentry/sentry",
        shallow=False,
        language="python",
        config=CodebaseConfig(
            secrets=Secrets(openai_key=open_ai_key, github_api_key=github_token),
            feature_flags=CodebaseFeatureFlags(
                sync_enabled=True,
            ),
        ),
    )
    review = run(codebase)
    print(review)

    print("Codebase analysis complete.")
