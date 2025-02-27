import docker
from docker.errors import NotFound

from codegen.cli.commands.start.docker_container import DockerContainer

CODEGEN_RUNNER_IMAGE = "codegen-runner"


class DockerFleet:
    containers: list[DockerContainer]

    def __init__(self, containers: list[DockerContainer]):
        self.containers = containers

    @classmethod
    def load(cls) -> "DockerFleet":
        try:
            client = docker.from_env()
            filters = {"ancestor": CODEGEN_RUNNER_IMAGE}
            containers = []
            for container in client.containers.list(all=True, filters=filters):
                if container.attrs["Config"]["Image"] == CODEGEN_RUNNER_IMAGE:
                    containers.append(DockerContainer(client=client, container=container))

            return cls(containers=containers)
        except NotFound:
            return cls(containers=[])

    @property
    def active_containers(self) -> list[DockerContainer]:
        return [container for container in self.containers if container.is_running()]

    def get(self, name: str) -> DockerContainer | None:
        return next((container for container in self.containers if container.name == name), None)

    def __str__(self) -> str:
        return f"DockerFleet(containers={',\n'.join(str(container) for container in self.containers)})"


if __name__ == "__main__":
    pool = DockerFleet.load()
    print(pool)
