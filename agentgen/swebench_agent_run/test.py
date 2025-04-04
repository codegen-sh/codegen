from codegen import Codebase
import modal

image = modal.Image.debian_slim(python_version="3.13").apt_install("git").pip_install("fastapi[standard]").run_commands("pip install codegen")

app = modal.App(name="codegen-examples", image=image, secrets=[modal.Secret.from_dotenv()])


@app.function()
def run_agent(AgentClass):
    codebase = Codebase.from_repo(repo_full_name="pallets/flask")
    agent = AgentClass(codebase)
    agent.run(prompt="Tell me about the codebase and the files in it.")
    return True
