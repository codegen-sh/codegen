"""Client for interacting with the locally hosted sandbox server hosted on a docker container."""

from codegen.cli.commands.start.docker_container import DockerContainer
from codegen.cli.commands.start.docker_fleet import DockerFleet
from codegen.cli.utils.function_finder import DecoratedFunction
from codegen.runner.clients.client import Client
from codegen.runner.models.apis import RUN_FUNCTION_ENDPOINT, RunFunctionRequest
from codegen.runner.models.codemod import CodemodRunResult


class DockerClient(Client):
    """Client for interacting with the locally hosted sandbox server hosted on a docker container."""

    def __init__(self, container: DockerContainer):
        if not container.is_running() or container.host is None or container.port is None:
            msg = f"Container {container.name} is not running."
            raise Exception(msg)
        super().__init__(container.host, container.port)

    def run(self, codemod_source: str, commit: bool | None = None) -> CodemodRunResult:
        req = RunFunctionRequest(function_name="unnamed", codemod_source=codemod_source, commit=commit)
        response = self.post(RUN_FUNCTION_ENDPOINT, req.model_dump())
        return CodemodRunResult.model_validate(response.json())

    def run_function(self, function: DecoratedFunction, commit: bool) -> CodemodRunResult:
        req = RunFunctionRequest(function_name=function.name, codemod_source=function.source, commit=commit)
        response = self.post(RUN_FUNCTION_ENDPOINT, req.model_dump())
        return CodemodRunResult.model_validate(response.json())


if __name__ == "__main__":
    fleet = DockerFleet.load()
    cur = next((container for container in fleet.containers if container.is_running()), None)
    if cur is None:
        msg = "No running container found. Run `codegen start` from a git repo first."
        raise Exception(msg)
    client = DockerClient(cur)
    print(f"healthcheck: {client.is_running()}")
    result = client.run("print(codebase)")
    print(result)
