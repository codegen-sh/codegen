from functools import cached_property

import docker
from docker import DockerClient
from docker.errors import APIError, NotFound
from docker.models.containers import Container


class DockerContainer:
    _client: DockerClient
    _container: Container | None

    def __init__(self, client: DockerClient, container: Container) -> None:
        self._client = client
        self._container = container

    @classmethod
    def get(cls, name: str) -> "DockerContainer | None":
        try:
            client = docker.from_env()
            container = client.containers.get(name)
            return cls(client=client, container=container)
        except NotFound:
            return None

    @cached_property
    def name(self) -> str:
        return self._container.name

    @cached_property
    def host(self) -> str | None:
        if not self.is_running():
            return None

        host_config = next(iter(self._container.ports.values()))[0]
        return host_config["HostIp"]

    @cached_property
    def port(self) -> int | None:
        if not self.is_running():
            return None

        host_config = next(iter(self._container.ports.values()))[0]
        return host_config["HostPort"]

    def is_running(self) -> bool:
        try:
            return self._container.status == "running"
        except NotFound:
            return False

    def start(self) -> bool:
        try:
            self._container.start()
            return True
        except (NotFound, APIError):
            return False

    def stop(self) -> bool:
        try:
            self._container.stop()
            return True
        except (NotFound, APIError):
            return False

    def remove(self) -> bool:
        try:
            self.stop()
            self._container.remove()
            return True
        except (NotFound, APIError):
            return False

    def __str__(self) -> str:
        return f"DockerSession(name={self.name}, host={self.host or 'unknown'}, port={self.port or 'unknown'})"
