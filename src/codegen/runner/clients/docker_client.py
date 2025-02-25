"""Client for interacting with the locally hosted sandbox server hosted on a docker container."""

from codegen.cli.commands.start.docker_container import DockerContainer
from codegen.cli.commands.start.docker_fleet import DockerFleet
from codegen.runner.clients.client import Client
from codegen.runner.models.apis import DIFF_ENDPOINT, GetDiffRequest
from codegen.runner.models.codemod import Codemod


class DockerClient(Client):
    """Client for interacting with the locally hosted sandbox server hosted on a docker container."""

    def __init__(self, container: DockerContainer):
        if not container.is_running() or container.host is None or container.port is None:
            msg = f"Container {container.name} is not running."
            raise Exception(msg)
        super().__init__(container.host, container.port)


if __name__ == "__main__":
    fleet = DockerFleet.load()
    cur = next((container for container in fleet.containers if container.is_running()), None)
    if cur is None:
        msg = "No running container found. Run `codegen start` from a git repo first."
        raise Exception(msg)
    client = DockerClient(cur)
    print(f"healthcheck: {client.healthcheck()}")
    codemod = Codemod(user_code="print(codebase)")
    diff_req = GetDiffRequest(codemod=codemod)
    res = client.post(DIFF_ENDPOINT, diff_req.model_dump())
    print(res.json())
