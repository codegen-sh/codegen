import docker

CODEGEN_RUNNER_IMAGE = "codegen-runner"


class DockerSession:
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


class DockerSessions:
    sessions: list[DockerSession]

    def __init__(self, sessions: list[DockerSession]):
        self.sessions = sessions

    @classmethod
    def load(cls) -> "DockerSessions":
        try:
            client = docker.from_env()
            containers = client.containers.list(all=True, filters={"ancestor": CODEGEN_RUNNER_IMAGE})
            sessions = []
            for container in containers:
                if container.attrs["Config"]["Image"] == CODEGEN_RUNNER_IMAGE:
                    if container.status == "running":
                        host_config = next(iter(container.ports.values()))[0]
                        session = DockerSession(client=client, host=host_config["HostIp"], port=host_config["HostPort"], name=container.name)
                    else:
                        session = DockerSession(client=client, name=container.name)
                    sessions.append(session)

            return cls(sessions=sessions)
        except docker.errors.NotFound:
            return cls(sessions=[])

    def get(self, name: str) -> DockerSession | None:
        return next((session for session in self.sessions if session.name == name), None)

    def __str__(self) -> str:
        return f"DockerSessions(sessions={',\n'.join(str(session) for session in self.sessions)})"


if __name__ == "__main__":
    docker_sessions = DockerSessions.load()
    print(docker_sessions)
