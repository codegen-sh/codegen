"""Client for interacting with the locally hosted sandbox server hosted on a docker container."""

from codegen.runner.clients.server_client import LocalServerClient


class DockerClient(LocalServerClient):
    """Client for interacting with the locally hosted sandbox server hosted on a docker container."""

    def __init__(self, repo_config: RepoConfig):
        super().__init__(repo_config, host, port)
