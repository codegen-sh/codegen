import socket
from contextlib import closing


def get_free_port() -> int:
    """Find and return a free port on localhost"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        return int(port)


def is_port_free(port: int, host: str = "localhost") -> bool:
    """Check if a port is free on localhost"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        return s.connect_ex((host, port)) != 0
