import modal

from codegen_on_oss.sources import GithubSettings, GithubSource

app = modal.App("codegen-oss-parse")


@app.local_entrypoint()
def main(
    languages: str = "python,typescript",
    heuristic: str = "stars",
    num_repos: int = 100,
):
    """
    Main entrypoint for the parse app.
    """
    parse_repo_on_modal_fn = modal.Function.from_name("codegen-oss-parse", "parse_repo")
    for language in languages.split(","):
        repo_source = GithubSource(
            GithubSettings(
                language=language.strip(), heuristic=heuristic, num_repos=num_repos
            )
        )
        for repo_url, commit_hash in repo_source:
            parse_repo_on_modal_fn.spawn(
                repo_url=repo_url,
                commit_hash=commit_hash,
                language=language,
            )
