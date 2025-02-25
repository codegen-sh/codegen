"""Client for interacting with the locally hosted sandbox server hosted on a docker container."""

from codegen.cli.commands.start.docker_session import DockerSession
from codegen.runner.clients.client import Client


class DockerClient(Client):
    """Client for interacting with the locally hosted sandbox server hosted on a docker container."""

    def __init__(self, docker_session: DockerSession):
        super().__init__(docker_session.host, docker_session.port)
