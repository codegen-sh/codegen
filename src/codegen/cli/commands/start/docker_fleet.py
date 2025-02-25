import docker

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
            containers = client.containers.list(all=True, filters={"ancestor": CODEGEN_RUNNER_IMAGE})
            codegen_containers = []
            for container in containers:
                if container.attrs["Config"]["Image"] == CODEGEN_RUNNER_IMAGE:
                    if container.status == "running":
                        host_config = next(iter(container.ports.values()))[0]
                        codegen_container = DockerContainer(client=client, host=host_config["HostIp"], port=host_config["HostPort"], name=container.name)
                    else:
                        codegen_container = DockerContainer(client=client, name=container.name)
                    codegen_containers.append(codegen_container)

            return cls(containers=codegen_containers)
        except docker.errors.NotFound:
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
