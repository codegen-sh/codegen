import docker


class DockerContainer:
    _client: docker.DockerClient
    host: str | None
    port: int | None
    name: str

    def __init__(self, client: docker.DockerClient, name: str, port: int | None = None, host: str | None = None):
        self._client = client
        self.host = host
        self.port = port
        self.name = name

    def is_running(self) -> bool:
        try:
            container = self._client.containers.get(self.name)
            return container.status == "running"
        except docker.errors.NotFound:
            return False

    def start(self) -> bool:
        try:
            container = self._client.containers.get(self.name)
            container.start()
            return True
        except (docker.errors.NotFound, docker.errors.APIError):
            return False

    def __str__(self) -> str:
        return f"DockerSession(name={self.name}, host={self.host or 'unknown'}, port={self.port or 'unknown'})"
