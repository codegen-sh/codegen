import click
import modal
from codegen import CodeAgent, Codebase

image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("codegen")

app = modal.App(
    name="codegen-examples",
    image=image,
    secrets=[modal.Secret.from_dotenv()],
)


@app.function()
def run_agent(repo_name: str, prompt: str) -> bool:
    codebase = Codebase.from_repo(repo_full_name=repo_name)
    agent = CodeAgent(codebase)
    return agent.run(prompt=prompt)


@click.command()
@click.option(
    "--repo",
    type=str,
    default="pallets/flask",
    help="The repository to analyze (format: owner/repo)",
)
@click.option(
    "--prompt",
    type=str,
    default="Tell me about the codebase and the files in it.",
    help="The prompt to send to the agent",
)
def main(repo: str, prompt: str):
    """Run a codegen agent on a GitHub repository."""
    # Import agent class dynamically based on name

    click.echo(f"Running on {repo}")
    click.echo(f"Prompt: {prompt}")

    try:
        with app.run():
            result = run_agent.remote(repo, prompt)
            if result:
                click.echo("✅ Analysis completed successfully:")
                click.echo(result)
            else:
                click.echo("❌ Analysis failed")
    except Exception as e:
        click.echo(f"❌ Error: {str(e)}", err=True)
        raise click.Abort()


if __name__ == "__main__":
    main()
